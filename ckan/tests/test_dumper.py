import tempfile
import simplejson
import os

import ckan
from ckan.tests import *
import ckan.model as model
import ckan.lib.dumper as dumper
from ckan.lib.dumper import Dumper
simple_dumper = dumper.SimpleDumper()

class TestSimpleDump(TestController):

    @classmethod
    def setup_class(self):
        model.repo.rebuild_db()
        CreateTestData.create()

    @classmethod
    def teardown_class(self):
        model.Session.remove()
        model.repo.rebuild_db()

    def test_simple_dump_csv(self):
        dump_file = tempfile.TemporaryFile()
        simple_dumper.dump(dump_file, 'csv')
        dump_file.seek(0)
        res = dump_file.read()
        assert 'annakarenina' in res, res
        assert 'russian tolstoy' in res, res
        assert 'genre' in res, res
        assert 'romantic novel' in res, res
        assert 'romantic novel' in res, res
        assert 'annakarenina.com/download' in res, res
        assert 'Index of the novel' in res, res
        
    def test_simple_dump_json(self):
        dump_file = tempfile.TemporaryFile()
        simple_dumper.dump(dump_file, 'json')
        dump_file.seek(0)
        res = dump_file.read()
        assert 'annakarenina' in res, res
        assert '"russian"' in res, res
        assert 'genre' in res, res
        assert 'romantic novel' in res, res

class TestDumper(object):
# TODO this doesn't work on sqlite - we should fix this
    @classmethod
    def setup_class(self):
        model.Session.remove()
        CreateTestData.create()
        d = Dumper()
        self.outpath = '/tmp/mytestdump.js'
        if os.path.exists(self.outpath):
            os.remove(self.outpath)
        d.dump_json(self.outpath)

    @classmethod
    def teardown_class(self):
        CreateTestData.delete()

    def test_dump(self):
        assert os.path.exists(self.outpath) 
        dumpeddata = simplejson.load(open(self.outpath))
        assert dumpeddata['version'] == ckan.__version__
        tables = dumpeddata.keys()
        for key in ['Package', 'Tag', 'Group', 'PackageGroup', 'PackageExtra']:
            assert key in tables, '%r not in %s' % (key, tables)
        for key in ['User']:
            assert key not in tables, '%s should not be in %s' % (key, tables)
        assert len(dumpeddata['Package']) == 2, len(dumpeddata['Package'])
        assert len(dumpeddata['Tag']) == 2, len(dumpeddata['Tag'])
        assert len(dumpeddata['PackageRevision']) == 2, len(dumpeddata['PackageRevision'])
        assert len(dumpeddata['Group']) == 2, len(dumpeddata['Group'])

    # Disabled 22/9/09 because not used anymore
    def _test_load(self):
        model.repo.clean_db()
        model.repo.create_db()
        d = Dumper()
        d.load_json(self.outpath)
        assert len(model.Package.query.all()) == 2
