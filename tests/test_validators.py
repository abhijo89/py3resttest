# -*- coding: utf-8 -*-
import unittest
from inspect import currentframe, getframeinfo
from pathlib import Path

from py3resttest import validators
from py3resttest.binding import Context
from py3resttest.constants import safe_length, regex_compare
from py3resttest.ext.validator_jsonschema import JsonSchemaValidator
from py3resttest.validators import register_extractor, _get_extractor, register_test, register_comparator


class ValidatorsTest(unittest.TestCase):
    """ Testing for validators and extract functions """

    def test_failure_obj(self):
        """ Tests the basic boolean override here """
        myfailure = validators.Failure()
        self.assertFalse(myfailure)

    def test_contains_operators(self):
        """ Tests the contains / contained_by """
        cont_func = validators.COMPARATORS['contains']
        cont_by_func = validators.COMPARATORS['contained_by']

        self.assertTrue(cont_func('abagooberab23', 'goob'))
        self.assertTrue(cont_by_func('goob', 'abagooberab23'))
        myarray = ['math', 1, None, u'lest']
        self.assertTrue(cont_func(myarray, 1))
        self.assertTrue(cont_func(myarray, None))
        self.assertTrue(cont_by_func(None, myarray))
        self.assertTrue(cont_func({'key': 'val'}, 'key'))
        self.assertTrue(cont_by_func('key', {'key': 'val'}))

        # Failure cases
        self.assertFalse(cont_func(None, 'test'))
        self.assertFalse(cont_by_func('test', None))
        self.assertFalse(cont_func(myarray, 'notinit'))
        self.assertFalse(cont_by_func('notinit', myarray))

    def test_type_comparator(self):
        """ Complex verification of the type test method, heh """

        type_test = validators.COMPARATORS['type']
        hasFailed = False
        instances = {
            'string': 'goober',
            'int': 1,
            'float': 0.5,
            'boolean': False,
            'number': 1,
            'array': [4, 'val'],
            'list': ['my', 1, None],
            'none': None,
            'null': None,
            'scalar': 4.0,
            'collection': ['collection', 1, None],
            'dict': {1: 'ring', 4: 1, 'gollum': 'smeagol'}
        }

        # Check for basic types that they pass expected values
        for mytype, myinstance in instances.items():
            try:
                self.assertTrue(type_test(myinstance, mytype))
            except AssertionError:
                print('Type test operator failed where should pass for type {0} and value {1}'.format(
                    mytype, myinstance))
                hasFailed = True

        if hasFailed:
            self.fail("Type test operator failed testing, see reasons above!")

    def test_type_comparator_failures(self):
        """ Test cases where type comparator should fail """
        type_test = validators.COMPARATORS['type']
        hasFailed = False

        failing_instances = {
            'string': 1,
            'int': {'nope': 3},
            'float': 3,
            'boolean': None,
            'number': 'lolz',
            'array': False,
            'list': 'string here',
            'none': 4,
            'scalar': {'key': 'val'},
            'collection': 'string',
            'dict': [1, 2, 3]
        }

        # Check for complex types that they don't pass expected values
        for mytype, myinstance in failing_instances.items():
            try:
                self.assertFalse(type_test(myinstance, mytype))
            except AssertionError:
                print('Type test operator passed where should fail for type {0} and value {1}'.format(
                    mytype, myinstance))
                hasFailed = True
        if hasFailed:
            self.fail("Type test operator failed testing, see reasons above!")

    def test_type_comparator_specialcases(self):
        """ Covers things such as case handling and exception throwing """
        type_test = validators.COMPARATORS['type']
        self.assertTrue(type_test('string', 'scALar'))
        self.assertTrue(type_test(None, 'scalar'))

        try:
            type_test(3, 'doesnotexist')
            self.fail(
                'Type test comparator throws exception if you test against an undefined type')
        except TypeError:
            pass

    def test_safe_length(self):
        self.assertEqual(1, safe_length('s'))
        self.assertEqual(2, safe_length(['text', 2]))
        self.assertEqual(2, safe_length({'key': 'val', 1: 2}))
        self.assertEqual(-1, safe_length(False))
        self.assertEqual(-1, safe_length(None))

    def test_regex_compare(self):
        txt = "Millie Finn Gaten"
        self.assertTrue(regex_compare(txt, "\s"))

    def test_validatortest_exists(self):
        func = validators.VALIDATOR_TESTS['exists']
        self.assertTrue(func('blah'))
        self.assertTrue(func(0))
        self.assertTrue(func('False'))
        self.assertTrue(func(False))
        self.assertFalse(func(None))

    def test_validatortest_not_exists(self):
        func = validators.VALIDATOR_TESTS['not_exists']
        self.assertFalse(func('blah'))
        self.assertFalse(func(0))
        self.assertFalse(func('False'))
        self.assertTrue(func(None))

    def test_dict_query(self):
        """ Test actual query logic """
        mydict = {'key': {'val': 3}}
        query = 'key.val'
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        self.assertEqual(3, val)

        array = [1, 2, 3]
        mydict = {'key': {'val': array}}
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        self.assertEqual(array, val)

        mydict = {'key': {'v': 'pi'}}
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        self.assertEqual(None, val)

        # Array test
        query = 'key.val.1'
        mydict = {'key': {'val': array}}
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        self.assertEqual(array[1], val)

        # Error cases
        query = 'key.val.5'
        mydict = {'key': {'val': array}}
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        self.assertEqual(None, val)

        query = 'key.val.pi'
        mydict = {'key': {'val': array}}
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        self.assertEqual(None, val)

        # Return the first object?
        query = 'key.0'
        mydict = {'key': {'val': array}}
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        self.assertEqual(None, val)

        # Mix array array and dictionary
        mydict = [{'key': 'val'}]
        query = '0.key'
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        self.assertEqual('val', val)

    def test_jsonpathmini_unicode(self):
        myjson = u'{"myVals": [0, 1.0, "😽"], "my😽":"value"}'

        query_normal = validators.MiniJsonExtractor.parse('myVals.2')
        self.assertEqual(u'😽', query_normal.extract(body=myjson))

        query_unicode = validators.MiniJsonExtractor.parse(u'my😽')
        self.assertEqual('value', query_unicode.extract(body=myjson))

    def test_jsonpathmini_wholeobject(self):
        """ Verify that the whole Json object can be returned by delimiter queries """

        myobj = {'key': {'val': 3}}
        query = ''
        val = validators.MiniJsonExtractor.query_dictionary(query, myobj)
        self.assertEqual(myobj, val)

        myobj = [{'key': 'val'}, 3.0, {1: 'val'}]
        val = validators.MiniJsonExtractor.query_dictionary(query, myobj)
        self.assertEqual(myobj, val)

        query = '.'
        val = validators.MiniJsonExtractor.query_dictionary(query, myobj)
        self.assertEqual(myobj, val)

        query = '..'
        val = validators.MiniJsonExtractor.query_dictionary(query, myobj)
        self.assertEqual(myobj, val)

    def test_parse_extractor_minijson(self):
        config = 'key.val'
        extractor = validators.MiniJsonExtractor.parse(config)
        myjson = '{"key": {"val": 3}}'
        context = Context()
        context.bind_variable('node', 'val')

        extracted = extractor.extract(body=myjson)
        self.assertEqual(3, extracted)
        self.assertEqual(extracted, extractor.extract(
            body=myjson, context=context))

        try:
            val = extractor.extract(body='[31{]')
            self.fail("Should throw exception on invalid JSON")
        except ValueError:
            pass

        # Templating
        config = {'template': 'key.$node'}
        extract = validators.MiniJsonExtractor.parse(config)
        self.assertEqual(3, extract.extract(myjson, context=context))

    def test_header_extractor(self):
        query = 'content-type'
        extractor = validators.HeaderExtractor.parse(query)
        headers = [('content-type', 'application/json')]
        extracted = extractor.extract(body='blahblah', headers=headers)
        self.assertEqual(headers[0][1], extracted)

        # Test case-insensitivity
        query = 'content-Type'
        extractor = validators.HeaderExtractor.parse(query)
        extracted = extractor.extract(body='blahblah', headers=headers)
        self.assertEqual(headers[0][1], extracted)

        # Throws exception if invalid header
        headers = [('foo', 'bar')]
        try:
            extracted = extractor.extract(body='blahblah', headers=headers)
            self.fail("Extractor should throw exception on invalid key")
        except ValueError:
            pass

    def test_header_extractor_duplicatekeys(self):
        # Test for handling of multiple headders
        query = 'content-Type'
        headers = [('content-type', 'application/json'),
                   ('content-type', 'x-json-special')]
        extractor = validators.HeaderExtractor.parse(query)
        extracted = extractor.extract(body='blahblah', headers=headers)
        self.assertTrue(isinstance(extracted, list))
        self.assertEqual(headers[0][1], extracted[0])
        self.assertEqual(headers[1][1], extracted[1])

    def test_parse_header_extractor(self):
        query = 'content-type'
        extractor = validators.parse_extractor('header', query)
        self.assertTrue(isinstance(extractor, validators.HeaderExtractor))
        self.assertTrue(extractor._is_header_extractor)
        self.assertFalse(extractor._is_body_extractor)

    def test_raw_body_extractor(self):
        query = ''
        extractor = validators.parse_extractor('raw_body', None)
        extractor = validators.parse_extractor('raw_body', query)
        self.assertTrue(isinstance(extractor, validators.RawBodyExtractor))
        self.assertTrue(extractor._is_body_extractor)
        self.assertFalse(extractor._is_header_extractor)

        bod = u'j1j21io312j3'
        val = extractor.extract(body=bod, headers='')
        self.assertEqual(bod, val)

        bod = b'j1j21io312j3'
        val = extractor.extract(body=bod, headers='')
        self.assertEqual(bod, val)

    def test_abstract_extractor_parse(self):
        """ Test parsing a basic abstract extractor """

        class A(validators.AbstractExtractor):
            def extract_internal(self, query=None, body=None, headers=None, args=None):
                ...

        ext = A()
        ext = validators.AbstractExtractor.configure_base('val', ext)
        self.assertEqual('val', ext.query)
        self.assertEqual(False, ext.is_templated)

        validators.AbstractExtractor.configure_base({'template': '$var'}, ext)
        self.assertEqual(True, ext.is_templated)
        self.assertEqual('$var', ext.query)

        self.assertRaises(ValueError, validators.AbstractExtractor.configure_base, {'template1': '$var'}, ext)
        self.assertRaises(TypeError, validators.AbstractExtractor.configure_base, 1, ext)

        self.assertRaises(Exception, _get_extractor, {'x': "test"})

    def test_abstract_extractor_string(self):
        """ Test abstract extractor to_string method """

        class A(validators.AbstractExtractor):
            def extract_internal(self, query=None, body=None, headers=None, args=None):
                return 1

        ext = A()
        ext.is_templated = True
        ext._is_header_extractor = True
        ext._is_body_extractor = True
        ext.query = 'gooblyglah'
        ext.extractor_type = 'bleh'
        ext.args = {'cheesy': 'poofs'}

        expected = "Extractor type: {0}, query: {1}, is_templated: {2}, args: {3}".format(
            ext.extractor_type, ext.query, ext.is_templated, ext.args)
        self.assertEqual(expected, str(ext))
        self.assertTrue(ext.is_body_extractor)
        self.assertEqual(ext.extract_internal(), 1)

    def test_abstract_extractor_templating(self):
        """ Test that abstract extractors template the query """

        class A(validators.AbstractExtractor):
            def extract_internal(self, query=None, body=None, headers=None, args=None):
                ...

        ext = A()
        ext.query = '$val.vee'
        ext.is_templated = True
        context = Context()
        context.bind_variable('val', 'foo')
        self.assertEqual('$val.vee', ext.templated_query())
        self.assertEqual('foo.vee', ext.templated_query(context=context))

        ext._is_templated = False
        self.assertEqual('$val.vee', ext.templated_query(context=context))

    def test_abstract_extractor_readableconfig(self):
        """ Test human-readable extractor config string output """
        config = 'key.val'
        extractor = validators.parse_extractor('jsonpath_mini', config)
        expected_string = 'Extractor Type: jsonpath_mini,  Query: "key.val", Templated?: False'
        self.assertEqual(expected_string, extractor.get_readable_config())

        # Check empty context & args uses okay
        context = Context()
        self.assertEqual(
            expected_string, extractor.get_readable_config(context=context))
        context.bind_variable('foo', 'bar')
        self.assertEqual(
            expected_string, extractor.get_readable_config(context=context))
        extractor.args = dict()
        self.assertEqual(
            expected_string, extractor.get_readable_config(context=context))

        # Check args output is handled correctly
        extractor.args = {'caseSensitive': True}
        self.assertEqual(expected_string + ", Args: " + str(extractor.args),
                         extractor.get_readable_config(context=context))

        # Check template handling is okay
        config = {'template': 'key.$templated'}
        context.bind_variable('templated', 'val')
        extractor = validators.parse_extractor('jsonpath_mini', config)
        expected_string = 'Extractor Type: jsonpath_mini,  Query: "key.val", Templated?: True'
        self.assertEqual(
            expected_string, extractor.get_readable_config(context=context))

    def test_parse_extractor(self):
        """ Test parsing an extractor using the registry """
        config = 'key.val'
        myjson = '{"key": {"val": 3}}'
        extractor = validators.parse_extractor('jsonpath_mini', config)
        self.assertTrue(isinstance(extractor, validators.AbstractExtractor))
        self.assertEqual(3, extractor.extract(body=myjson))

    def test_get_extractor(self):
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'eq',
            'expected': 3
        }
        extractor = validators._get_extractor(config)
        myjson = u'{"key": {"val": 3}}'
        extracted = extractor.extract(body=myjson)
        self.assertEqual(3, extracted)

        myjson = b'{"key": {"val": 3}}'
        extracted = extractor.extract(body=myjson)
        self.assertEqual(3, extracted)

    def test_parse_validator(self):
        """ Test basic parsing using registry """
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'eq',
            'expected': 3
        }
        validator = validators.parse_validator('comparator', config)
        myjson = '{"key": {"val": 3}}'
        comp = validator.validate(body=myjson)
        self.assertTrue(comp)

        validator = validators.parse_validator('comparator', config)
        my_body_str = '<html></html>'
        comp = validator.validate(body=my_body_str)
        self.assertEqual(comp.message, 'Extractor threw exception')

        validator = validators.parse_validator('comparator', config)
        myjson_1 = '{"key": {"val": 4}}'
        comp = validator.validate(body=myjson_1)
        self.assertFalse(comp)

        # Try it with templating
        # Try it with templating
        config['jsonpath_mini'] = {'template': 'key.$node'}
        validator = validators.parse_validator('comparator', config)
        context = Context()
        context.bind_variable('node', 'val')
        comp = validator.validate(myjson, context=context)
        self.assertTrue(comp)

        # Try it with templating
        del config['jsonpath_mini']
        config['jmespath'] = {'template': 'key.$node'}
        validator = validators.parse_validator('comparator', config)
        context = Context()
        context.bind_variable('node', 'val')
        comp = validator.validate(myjson, context=context)
        self.assertTrue(comp)

    def test_register_extractor(self):
        self.assertRaises(TypeError, register_extractor, 1, lambda x: x)
        self.assertRaises(ValueError, register_extractor, 'comparator', lambda x: x)
        self.assertRaises(ValueError, register_extractor, 'test', lambda x: x)
        self.assertRaises(ValueError, register_extractor, 'expected', lambda x: x)
        self.assertRaises(ValueError, register_extractor, 'jsonpath_mini', lambda x: x)

    def test_register_test(self):
        self.assertRaises(TypeError, register_test, 1, lambda x: x)
        self.assertRaises(ValueError, register_test, 'exists', lambda x: x)

    def test_register_comparator(self):
        self.assertRaises(TypeError, register_comparator, 1, lambda x: x)
        self.assertRaises(ValueError, register_comparator, 'count_eq', lambda x: x)

    def test_parse_wrong_comparator(self):
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'eq1',
            'expected': 3
        }
        self.assertRaises(ValueError, validators.parse_validator, 'comparator', config)

    def test_parse_validator_nocomparator(self):
        """ Test that comparator validator with no comparator defaults to eq """
        config = {
            'jsonpath_mini': 'key.val',
            'expected': 3
        }
        validator = validators.parse_validator('assertEqual', config)
        self.assertEqual('eq', validator.comparator_name)
        self.assertEqual(validators.COMPARATORS['eq'], validator.comparator)

    def test_validator_compare_eq(self):
        """ Basic test of the equality validator"""
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'eq',
            'expected': 3
        }
        comp_validator = validators.ComparatorValidator.parse(config)
        myjson_pass = '{"id": 3, "key": {"val": 3}}'
        myjson_fail = '{"id": 3, "key": {"val": 4}}'

        self.assertTrue(comp_validator.validate(body=myjson_pass))
        self.assertFalse(comp_validator.validate(body=myjson_fail))

    def test_validator_unicode_comparison(self):
        """ Checks for implicit unicode -> byte conversion in testing """
        config = {
            'raw_body': '.',
            'comparator': 'contains',
            'expected': u'stuff'
        }
        comp_validator = validators.ComparatorValidator.parse(config)
        myjson_pass = b'i contain stuff because win'
        myjson_fail = b'i fail without it'
        self.assertTrue(comp_validator.validate(body=myjson_pass))
        self.assertFalse(comp_validator.validate(body=myjson_fail))

        # Let's try this with unicode characters just for poops and giggles
        config = {
            'raw_body': '.',
            'comparator': 'contains',
            'expected': u'cat😽stuff'
        }
        myjson_pass = u'i contain cat😽stuff'.encode('utf-8')
        myjson_pass_unicode = u'i contain encoded cat😽stuff'
        self.assertTrue(comp_validator.validate(body=myjson_pass))
        self.assertTrue(comp_validator.validate(body=myjson_pass_unicode))

    def test_validator_compare_ne(self):
        """ Basic test of the inequality validator"""
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'ne',
            'expected': 3
        }
        comp_validator = validators.ComparatorValidator.parse(config)
        myjson_pass = '{"id": 3, "key": {"val": 4}}'
        myjson_fail = '{"id": 3, "key": {"val": 3}}'

        self.assertTrue(comp_validator.validate(body=myjson_pass))
        self.assertFalse(comp_validator.validate(body=myjson_fail))

    def test_validator_compare_not_equals(self):
        """ Basic test of the inequality validator alias"""
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'ne',
            'expected': 3
        }
        comp_validator = validators.ComparatorValidator.parse(config)
        myjson_pass = '{"id": 3, "key": {"val": 4}}'
        myjson_fail = '{"id": 3, "key": {"val": 3}}'

        self.assertTrue(comp_validator.validate(body=myjson_pass))
        self.assertFalse(comp_validator.validate(body=myjson_fail))

    def test_validator_comparator_templating(self):
        """ Try templating comparator validator """
        config = {
            'jsonpath_mini': {'template': 'key.$node'},
            'comparator': 'eq',
            'expected': 3
        }
        context = Context()
        context.bind_variable('node', 'val')
        myjson_pass = '{"id": 3, "key": {"val": 3}}'
        myjson_fail = '{"id": 3, "key": {"val": 4}}'
        comp = validators.ComparatorValidator.parse(config)

        self.assertTrue(comp.validate(body=myjson_pass, context=context))
        self.assertFalse(comp.validate(body=myjson_fail, context=context))

        # Template expected
        config['expected'] = {'template': '$id'}
        context.bind_variable('id', 3)
        self.assertTrue(comp.validate(body=myjson_pass, context=context))
        self.assertFalse(comp.validate(body=myjson_fail, context=context))

    def test_validator_comparator_extract(self):
        """ Try comparing two extract expressions """
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'eq',
            'expected': {'jsonpath_mini': 'id'}
        }
        myjson_pass = '{"id": 3, "key": {"val": 3}}'
        myjson_fail = '{"id": 3, "key": {"val": 4}}'
        comp = validators.ComparatorValidator.parse(config)
        self.assertTrue(comp.validate(body=myjson_pass))
        failure = comp.validate(body=myjson_fail)
        self.assertFalse(failure)

    def test_validator_error_responses(self):
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'eq',
            'expected': 3
        }
        comp = validators.ComparatorValidator.parse(config)
        myjson_fail = '{"id": 3, "key": {"val": 4}}'
        failure = comp.validate(body=myjson_fail)

        # Test the validator failure object handling
        self.assertFalse(failure)
        self.assertEqual(
            failure.message, 'Comparison failed, evaluating eq(4, 3) returned False')
        self.assertEqual(failure.message, str(failure))
        self.assertEqual(failure.failure_type,
                         validators.FAILURE_VALIDATOR_FAILED)
        expected_details = 'Extractor: Extractor Type: jsonpath_mini,  Query: "key.val", Templated?: False'
        self.assertEqual(expected_details, failure.details)
        self.assertEqual(comp, failure.validator)

        failure = comp.validate(body='{"id": 3, "key": {"val": 4}')
        self.assertTrue(isinstance(failure, validators.Failure))

    def test_parse_validator_jmespath_extracttest(self):
        """ Test parsing for jmespath extract test """
        try:
            import jmespath
            from ext.extractor_jmespath import JMESPathExtractor
            if not validators.EXTRACTORS.get('jmespath'):
                register_extractor('jmespath', JMESPathExtractor.parse)
            config = {
                'jmespath': 'key.val',
                'test': 'exists'
            }
            myjson_pass = '{"id": 3, "key": {"val": 3}}'
            myjson_fail = '{"id": 3, "key": {"valley": "wide"}}'
            validator = validators.ExtractTestValidator.parse(config)

            validation_result = validator.validate(body=myjson_pass)
            self.assertTrue(validation_result)

            validation_result = validator.validate(body=myjson_fail)
            self.assertFalse(validation_result)

            self.assertTrue(isinstance(validation_result, validators.Failure))
            self.assertEqual(validation_result.message,
                             "Extract and test validator failed on test: exists(None)")
        except ImportError:
            pass  # Doesn't run JMESPath test if can't import library

    def test_parse_validator_jsonpath_mini_extracttest(self):
        """ Test parsing for jsonpath_mini extract test """
        config = {
            'jsonpath_mini': 'key.val',
            'test': 'exists'
        }
        json_pass = '{"id": 3, "key": {"val": 3}}'
        json_fail = '{"id": 3, "key": {"valley": "wide"}}'
        validator = validators.ExtractTestValidator.parse(config)
        validation_result = validator.validate(body=json_pass)
        self.assertTrue(validation_result)
        validator = validators.ExtractTestValidator.parse(config)
        validation_result = validator.validate(body=json_fail)
        self.assertFalse(validation_result)
        self.assertTrue(isinstance(validation_result, validators.Failure))
        self.assertEqual(validation_result.message,
                         "Extract and test validator failed on test: exists(None)")

    def test_jsonschama(self):
        filename = getframeinfo(currentframe()).filename
        current_module_path = Path(filename)
        file = str(current_module_path.parent) + "/miniapp-schema.json"
        with open(file) as f:
            config = {
                'schema': f.read()
            }
        comp_validator = JsonSchemaValidator.parse(config)
        myjson_pass = bytes('{"id": 3 }', 'utf-8')
        myjson_fail = str({"id": 3, })
        self.assertEqual(comp_validator.validate(body=myjson_fail).message, "Invalid response json body")
        result = comp_validator.validate(body=myjson_pass)
        self.assertTrue(result)

        myjson_pass = bytes('{"id1": "id" }', 'utf-8')
        self.assertFalse(comp_validator.validate(body=myjson_pass))
        self.assertRaises(ValueError, JsonSchemaValidator.parse, {'x': 20})
        self.assertEqual(comp_validator.get_readable_config(), "JSON schema validation")

if __name__ == '__main__':
    unittest.main()
