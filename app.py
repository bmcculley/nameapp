#!/usr/bin/env python
from __future__ import division
import bcrypt
import concurrent.futures
import MySQLdb
import os.path
import re
import subprocess
import json
import torndb
import tornado.escape
from tornado import gen
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata
import math
from datetime import datetime

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="database host")
define("mysql_database", default="nameapp", help="database name")
define("mysql_user", default="username", help="database user")
define("mysql_password", default="password", help="database password")


# A thread pool to be used for password hashing with bcrypt.
executor = concurrent.futures.ThreadPoolExecutor(2)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/create", ComposeHandler),
            (r"/auth/create", AuthCreateHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
        ]
        settings = dict(
            site_title=u"Name App",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules={"Person": PersonModule},
            xsrf_cookies=True,
            cookie_secret="cookie_secret",
            login_url="/auth/login",
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)
        # Have one global connection to the blog DB across all handlers
        self.db = torndb.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)

        self.maybe_create_tables()

    def maybe_create_tables(self):
        try:
            self.db.get("SELECT COUNT(*) from persons;")
        except MySQLdb.ProgrammingError:
            subprocess.check_call(['mysql',
                                   '--host=' + options.mysql_host,
                                   '--database=' + options.mysql_database,
                                   '--user=' + options.mysql_user,
                                   '--password=' + options.mysql_password],
                                  stdin=open('db.sql'))


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def is_ajax(self):
        return bool("X-Requested-With" in self.request.headers and \
            self.request.headers['X-Requested-With'] == "XMLHttpRequest")

    def get_current_user(self):
        user_id = self.get_secure_cookie("nademo_user")
        if not user_id: return None
        return self.db.get("SELECT * FROM users WHERE id = %s", int(user_id))

    def admin_exists(self):
        return bool(self.db.get("SELECT * FROM users WHERE access_level = 10 LIMIT 1"))

    def validate_date(self, d):
        try:
            datetime.strptime(d, '%Y-%m-%d')
            return True
        except ValueError:
            return False


class HomeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):

        # do some pagination
        prev_page = None
        next_page = None
        current_page = self.get_argument("page", 1)
        if current_page:
            current_page = int(current_page)
        items_per_page = 10
        row_count = self.db.query("SELECT id FROM persons ORDER BY id "
                                "DESC LIMIT 1")
        row_count = int(row_count[0]["id"])
        
        total_pages = int(math.ceil(row_count/items_per_page))
        
        if current_page >= 2:
            prev_page = current_page-1
        if current_page < total_pages:
            next_page = current_page+1

        # grab the results
        limit_id = row_count + 1
        
        if current_page > 1:
            limit_id = limit_id - (items_per_page * (current_page-1))
        
        persons = self.db.query("SELECT * FROM persons where id < %i ORDER BY id "
                                "DESC LIMIT 10"% limit_id)
        if not persons:
            self.redirect("/create")
            return
        self.render("home.html", persons=persons, prevpage=prev_page, nextpage=next_page)


class ComposeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        id = self.get_argument("id", None)
        delete = self.get_argument("d", None)

        if delete and id:
            in_id = self.db.execute("DELETE FROM persons where id = %s"% int(id))
            self.redirect("/")

        entry = None
        if id:
            entry = self.db.get("SELECT * FROM persons WHERE id = %s", int(id))
        if self.is_ajax():
            self.render("ajax_compose.html", entry=entry)
        else:
            self.render("create.html", entry=entry)

    @tornado.web.authenticated
    def post(self):
        id = self.get_argument("id", None)

        firstname = self.get_argument("firstname")
        lastname = self.get_argument("lastname")
        # need to validate the date format
        dob = self.get_argument("dob")
        zip_code = self.get_argument("zip_code")

        if dob:
            if not self.validate_date(dob):
                if self.is_ajax():
                    data = {"error":"true","message":"Date format is invalid."}
                    self.write(data)
                    return
                else:
                    # need to modify template to handle error messages
                    self.redirect("/")


        if id:
            entry = self.db.get("SELECT * FROM persons WHERE id = %s", int(id))
            if not entry: raise tornado.web.HTTPError(404)
            self.db.execute(
                "UPDATE persons SET firstname = %s, lastname = %s, dob = %s, zip_code = %s "
                "WHERE id = %s", firstname, lastname, dob, zip_code, int(id))
        else:
            in_id = self.db.execute(
                "INSERT INTO persons (author_id,firstname,lastname,dob,zip_code"
                ") VALUES (%s,%s,%s,%s,%s)",
                self.current_user.id, firstname, lastname, dob, zip_code)
        if self.is_ajax():
            in_id = "%s"% str(in_id)
            data = {"error":"false","message":"Person successfully created","in_id":in_id}
            self.write(data)
            return
        else:
            self.redirect("/")

# modify this so an admin can create more admins... :-D
class AuthCreateHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        cur_access_level = self.get_current_user()['access_level']
        if cur_access_level < 10:
            self.render("no_access.html")
        else:
            self.render("create_user.html")

    @gen.coroutine
    def post(self):
        access_level = 1
        hashed_password = yield executor.submit(
            bcrypt.hashpw, tornado.escape.utf8(self.get_argument("password")),
            bcrypt.gensalt())
        user_id = self.db.execute(
            "INSERT INTO users (email, name, hashed_password, access_level) "
            "VALUES (%s, %s, %s, %s)",
            self.get_argument("email"), self.get_argument("name"),
            hashed_password, access_level)
        #self.set_secure_cookie("nademo_user", str(user_id))
        self.redirect(self.get_argument("next", "/"))


class AuthLoginHandler(BaseHandler):
    def get(self):
        print repr(self.request.remote_ip)
        # If there isn't an admin, redirect to the account creation page.
        if not self.admin_exists():
            self.redirect("/auth/create")
        else:
            self.render("login.html", error=None)

    @gen.coroutine
    def post(self):
        ajax = False
        if self.is_ajax():
            # handle ajax request
            ajax = True

        user = self.db.get("SELECT * FROM users WHERE name = %s OR email = %s",
                             self.get_argument("email"), self.get_argument("email"))

        if not user:
            if ajax:
                data = {"error":"true","message":"user not found"}
                self.write(data)
                return
            else:
                self.render("login.html", error="user not found")
                return
        hashed_password = yield executor.submit(
            bcrypt.hashpw, tornado.escape.utf8(self.get_argument("password")),
            tornado.escape.utf8(user.hashed_password))
        if hashed_password == user.hashed_password:
            self.set_secure_cookie("nademo_user", str(user.id))
            if ajax:
                data = {"error":"false","message":"login successful","cookie_data":self.xsrf_token}
                self.write(data)
                return
            else:
                self.redirect(self.get_argument("next", "/"))
        else:
            if ajax:
                data = {"error":"true","message":"incorrect password"}
                self.write(data)
                return
            else:
                self.render("login.html", error="incorrect password")


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("nademo_user")
        self.redirect(self.get_argument("next", "/"))


class PersonModule(tornado.web.UIModule):
    def render(self, person):
        return self.render_string("modules/person.html", person=person)


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
