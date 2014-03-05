import sqlalchemy as sa
from sqlalchemy.sql.expression import and_
from twisted.python import log
from buildbot.db import base

class UsDict(dict):
    pass

class User_realConnectorComponent(base.DBConnectorComponent):
    # Documentation is in developer/database.rst

    def getUser_realByUsername(self, username):
        def thd(conn):
            tbl = self.db.model.user_real
            log.msg("username=",username)
            q = tbl.select(whereclause=(tbl.c.username == username))
            user_real_row = conn.execute(q).fetchone()
            log.msg("user_real_row", user_real_row)
            if not user_real_row:
                return None

            # make UsDict to return
            usdict = UsDict()

            usdict['disp_name'] = user_real_row.display_name
            usdict['email'] = user_real_row.email
            log.msg("usdict", usdict)
            return usdict
        d = self.db.pool.do(thd)
        return d

    def getUsers(self):
        def thd(conn):
            tbl = self.db.model.user_real
            rows = conn.execute(tbl.select()).fetchall()
            log.msg("rows=",rows)
            dicts = []
            if rows:
                for row in rows:
                    ud = dict(username=row.username, dispname=row.display_name, email=row.email)
                    dicts.append(ud)
            return dicts
        d = self.db.pool.do(thd)
        return d


