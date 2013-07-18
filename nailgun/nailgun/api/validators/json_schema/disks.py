# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


disks_simple_format_schema = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'title': 'Disks',
    'description': 'Array of disks in simple format',
    'type': 'array',
    'items': {
        'type': 'object',
        'required': ['id', 'size', 'volumes'],
        'properties': {
            'id': {
                'description': 'The unique identifier for a disk',
                'type': 'string'
            },
            'size': {
                'description': 'Disk size in megabytes',
                'type': 'integer'
            },
            'volumes': {
                'description': 'Volumes for disk',
                'type': 'array',
                'items': {
                    'type': 'object',
                    'required': ['size', 'name'],
                    'properties': {
                        'name': {
                            'description': 'Volume name',
                            'type': 'string'
                        },
                        'size': {
                            'description': 'Volume size',
                            'type': 'integer'
                        }
                    }
                }
            }
        }
    }
}
