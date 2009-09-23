import simplejson

import ckan.model as model
from ckan.tests import *
from ckan.lib.base import *
import ckan.authz as authz

class TestPackageEditAuthz(TestController2):
    @classmethod
    def setup_class(self):
        model.repo.rebuild_db()
        model.repo.new_revision()
        self.admin = 'madeup-administrator'
        user = model.User(name=unicode(self.admin))
        self.pkgname = u'test6'
        pkg = model.Package(name=self.pkgname)
        model.setup_default_user_roles(pkg, admins=[user])

        model.repo.commit_and_remove()

    @classmethod
    def teardown_class(self):
        model.repo.rebuild_db()

    def test_0_nonadmin_cannot_edit_authz(self):
        offset = url_for(controller='package', action='authz', id=self.pkgname)
        res = self.app.get(offset, status=[302, 401])
        res = res.follow()
        assert res.request.url.startswith('/user/login')
        # Alternative if we allowed read-only access
        # res = self.app.get(offset)
        # assert not '<form' in res, res
    
    def test_1_admin_has_access(self):
        offset = url_for(controller='package', action='authz', id=self.pkgname)
        res = self.app.get(offset, extra_environ={'REMOTE_USER':
            self.admin})
    
    def test_2_read_ok(self):
        offset = url_for(controller='package', action='authz', id=self.pkgname)
        res = self.app.get(offset, extra_environ={'REMOTE_USER':
            self.admin})
        print res
        assert self.pkgname in res
        assert '<tr' in res
        assert self.admin in res
        assert 'Role' in res
        for uname in [ model.PSEUDO_USER__VISITOR, self.admin ]:
            assert '%s' % uname in res
        assert '<option value="__null_value__">' not in res
        # crude but roughly correct
        pkg = model.Package.by_name(self.pkgname)
        for r in pkg.roles:
            assert '<select id="PackageRole-%s-role' % r.id in res

        # now test delete links
        pr = pkg.roles[0]
        href = '%s' % pr.id
        assert href in res, res

    def test_3_admin_changes_role(self):
        offset = url_for(controller='package', action='authz', id=self.pkgname)
        res = self.app.get(offset, extra_environ={'REMOTE_USER':
            self.admin})
        assert self.pkgname in res

        def _r(r):
            return 'PackageRole-%s-role' % r.id
        def _u(r):
            return 'PackageRole-%s-user_id' % r.id
        def _prs(p):
            return dict([ (getattr(r.user, 'name', 'USER NAME IS NONE'), r) for r in pkg.roles ])

        pkg = model.Package.by_name(self.pkgname)
        prs = _prs(pkg)
        assert prs['visitor'].role == model.Role.EDITOR
        assert prs['logged_in'].role == model.Role.EDITOR
        form = res.forms[0]
        # change role assignments
        form.select(_r(prs['visitor']), model.Role.READER)
        form.select(_r(prs['logged_in']), model.Role.ADMIN)
        res = form.submit('commit', extra_environ={'REMOTE_USER': self.admin})

        model.Session.remove()
        pkg = model.Package.by_name(self.pkgname)
        prs = _prs(pkg)
        assert len(pkg.roles) == 3, prs
        assert prs['visitor'].role == model.Role.READER
        assert prs['logged_in'].role == model.Role.ADMIN
    
    def test_4_admin_deletes_role(self):
        pkg = model.Package.by_name(self.pkgname)
        assert len(pkg.roles) == 3
        # make sure not admin
        pr_id = [ r for r in pkg.roles if r.user.name != self.admin ][0].id
        offset = url_for(controller='package', action='authz', id=self.pkgname,
                role_to_delete=pr_id)
        # need this here as o/w conflicts over session binding
        model.Session.remove()
        res = self.app.get(offset, extra_environ={'REMOTE_USER':
            self.admin})
        assert 'Deleted role' in res, res
        pkg = model.Package.by_name(self.pkgname)
        assert len(pkg.roles) == 2
        assert model.PackageRole.query.filter_by(id=pr_id).count() == 0
