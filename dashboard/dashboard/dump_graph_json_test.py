# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import unittest

import webapp2
import webtest

from google.appengine.ext import ndb

from dashboard import dump_graph_json
from dashboard.common import testing_common
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.models import graph_data
from dashboard.models import sheriff


class DumpGraphJsonTest(testing_common.TestCase):

  def setUp(self):
    super(DumpGraphJsonTest, self).setUp()
    app = webapp2.WSGIApplication([(
        '/dump_graph_json', dump_graph_json.DumpGraphJsonHandler)])
    self.testapp = webtest.TestApp(app)

  def testGet_DumpJson_Basic(self):
    # Insert a test with no rows or alerts.
    testing_common.AddTests('M', 'b', {'foo': {}})

    # When a request is made for this one test, three entities should
    # be returned: the Master, Bot and TestMetadata entities.
    response = self.testapp.get('/dump_graph_json', {'test_path': 'M/b/foo'})
    protobuf_strings = json.loads(response.body)
    entities = list(
        map(dump_graph_json.BinaryProtobufToEntity, protobuf_strings))
    self.assertEqual(3, len(entities))
    masters = _EntitiesOfKind(entities, 'Master')
    bots = _EntitiesOfKind(entities, 'Bot')
    tests = _EntitiesOfKind(entities, 'TestMetadata')
    self.assertEqual('M', masters[0].key.string_id())
    self.assertEqual('b', bots[0].key.string_id())
    self.assertEqual('M/b/foo', tests[0].key.string_id())

  def testGet_DumpJson_WithRows(self):
    # Insert a test with rows.
    testing_common.AddTests('M', 'b', {'foo': {}})
    test_key = utils.TestKey('M/b/foo')
    test_container_key = utils.GetTestContainerKey(test_key)
    rows = []
    # The upper limit for revision numbers in this test; this was added
    # so that the test doesn't depend on the value of _DEFAULT_MAX_POINTS.
    highest_rev = 2000 + dump_graph_json._DEFAULT_MAX_POINTS - 1
    for rev in range(1000, highest_rev + 1):
      row = graph_data.Row(parent=test_container_key, id=rev, value=(rev * 2))
      rows.append(row)
    ndb.put_multi(rows)

    # There is a maximum number of rows returned by default, and the rows
    # are listed with latest revisions first.
    response = self.testapp.get(
        '/dump_graph_json',
        {'test_path': 'M/b/foo'})
    protobuf_strings = json.loads(response.body)
    entities = list(
        map(dump_graph_json.BinaryProtobufToEntity, protobuf_strings))
    out_rows = _EntitiesOfKind(entities, 'Row')
    expected_num_rows = dump_graph_json._DEFAULT_MAX_POINTS
    self.assertEqual(expected_num_rows, len(out_rows))
    expected_rev_range = range(
        highest_rev, highest_rev + 1 - expected_num_rows, -1)
    for expected_rev, row in zip(expected_rev_range, out_rows):
      self.assertEqual(expected_rev, row.revision)
      self.assertEqual(expected_rev * 2, row.value)

    # Specifying end_rev sets the final revision.
    response = self.testapp.get(
        '/dump_graph_json',
        {'test_path': 'M/b/foo', 'end_rev': 1199})
    protobuf_strings = json.loads(response.body)
    entities = list(
        map(dump_graph_json.BinaryProtobufToEntity, protobuf_strings))
    out_rows = _EntitiesOfKind(entities, 'Row')
    expected_num_rows = min(dump_graph_json._DEFAULT_MAX_POINTS, 200)
    self.assertEqual(expected_num_rows, len(out_rows))
    self.assertEqual(1199, out_rows[0].revision)

    # An alternative max number of rows can be specified.
    response = self.testapp.get(
        '/dump_graph_json',
        {'test_path': 'M/b/foo', 'num_points': 4})
    protobuf_strings = json.loads(response.body)
    entities = list(
        map(dump_graph_json.BinaryProtobufToEntity, protobuf_strings))
    out_rows = _EntitiesOfKind(entities, 'Row')
    rev_nums = [row.revision for row in out_rows]
    expected_rev_range = range(highest_rev, highest_rev - 4, -1)
    self.assertEqual(expected_rev_range, rev_nums)

  def testDumpJsonWithAlertData(self):
    testing_common.AddTests('M', 'b', {'foo': {}})
    test_key = utils.TestKey('M/b/foo')
    sheriff_key = sheriff.Sheriff(email='example@google.com').put()
    anomaly.Anomaly(sheriff=sheriff_key, test=test_key).put()

    # Anomaly entities for the requested test, as well as sheriffs for
    # the aforementioned Anomaly, should be returned.
    response = self.testapp.get(
        '/dump_graph_json',
        {'test_path': 'M/b/foo'})
    protobuf_strings = json.loads(response.body)
    self.assertEqual(5, len(protobuf_strings))
    entities = list(
        map(dump_graph_json.BinaryProtobufToEntity, protobuf_strings))
    anomalies = _EntitiesOfKind(entities, 'Anomaly')
    sheriffs = _EntitiesOfKind(entities, 'Sheriff')
    self.assertEqual(1, len(anomalies))
    self.assertEqual(1, len(sheriffs))
    self.assertEqual('example@google.com', sheriffs[0].email)

  def testGet_DumpAnomaliesDataForSheriff(self):
    # Insert some test, sheriffs and alerts.
    testing_common.AddTests('M', 'b', {'foo': {}})
    testing_common.AddTests('M', 'b', {'bar': {}})
    test_key_foo = utils.TestKey('M/b/foo')
    test_key_bar = utils.TestKey('M/b/bar')
    test_con_foo_key = utils.GetTestContainerKey(test_key_foo)
    test_con_bar_key = utils.GetTestContainerKey(test_key_bar)
    chromium_sheriff = sheriff.Sheriff(
        id='Chromium Perf Sheriff', email='chrisphan@google.com').put()
    qa_sheriff = sheriff.Sheriff(
        id='QA Perf Sheriff', email='chrisphan@google.com').put()
    anomaly.Anomaly(sheriff=chromium_sheriff, test=test_key_foo).put()
    anomaly.Anomaly(sheriff=qa_sheriff, test=test_key_bar).put()
    default_max_points = dump_graph_json._DEFAULT_MAX_POINTS

    # Add some rows.
    rows = []
    for rev in range(1, default_max_points * 2):
      row = graph_data.Row(parent=test_con_foo_key, id=rev, value=(rev * 2))
      rows.append(row)
      row = graph_data.Row(parent=test_con_bar_key, id=rev, value=(rev * 2))
      rows.append(row)
    ndb.put_multi(rows)

    # Anomaly entities, Row entities, TestMetadata, and Sheriff entities for
    # parameter 'sheriff' should be returned.
    response = self.testapp.get(
        '/dump_graph_json',
        {'sheriff': 'Chromium Perf Sheriff'})
    protobuf_strings = json.loads(response.body)
    self.assertEqual(default_max_points + 5, len(protobuf_strings))
    entities = list(
        map(dump_graph_json.BinaryProtobufToEntity, protobuf_strings))
    rows = _EntitiesOfKind(entities, 'Row')
    anomalies = _EntitiesOfKind(entities, 'Anomaly')
    sheriffs = _EntitiesOfKind(entities, 'Sheriff')
    self.assertEqual(default_max_points, len(rows))
    self.assertEqual(1, len(anomalies))
    self.assertEqual(1, len(sheriffs))
    self.assertEqual('Chromium Perf Sheriff', sheriffs[0].key.string_id())

  def testGet_NoTestPath_ReturnsError(self):
    # If no test path is given, an error is reported.
    self.testapp.get('/dump_graph_json', {}, status=500)

  def testGet_InvalidTestPath_ReturnsError(self):
    # If a wrong test path is given, JSON for an empty list is returned.
    response = self.testapp.get('/dump_graph_json', {'test_path': 'x'})
    self.assertEqual('[]', response.body)


def _EntitiesOfKind(entities, kind):
  """Returns a sublist of entities that are of a certain kind."""
  return [e for e in entities if e.key.kind() == kind]


if __name__ == '__main__':
  unittest.main()
