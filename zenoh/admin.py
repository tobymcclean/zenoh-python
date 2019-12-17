# Copyright (c) 2018 ADLINK Technology Inc.
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
# which is available at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
#
# Contributors: Angelo Corsaro, ADLINK Technology Inc. - Zenoh API refactoring

from zenoh.value import Value
from zenoh.encoding import Encoding
import zenoh.net


class Admin(object):
    '''
    The Administration helper class.
    '''

    PREFIX = '@'

    def __init__(self, ws):
        self.ws = ws
        self.local = ''.join('{:02x}'.format(x) for x in
                             ws.rt.info()[zenoh.net.ZN_INFO_PEER_PID_KEY])

    def add_backend(self, beid, properties, zid=None):
        '''
        Add a backend in the specified Zenoh router.

        :param beid: the Id of the backend.
        :param propertiers: some configuration for the backend.
        :param zid: the UUID of the Zenoh router. If ``None``, the local
            Zenoh router.
        '''
        if(zid is None):
            zid = self.local
        path = '/{}/{}/plugins/yaks/backend/{}'.format(
            Admin.PREFIX, zid, beid)
        value = Value(properties, encoding=Encoding.PROPERTY)
        return self.ws.put(path, value)

    def get_backends(self, zid=None):
        '''
        Get all the backends from the specified Zenoh router.

        :param zid: the UUID of the Zenoh router. If ``None``, the local
            Zenoh router.
        '''
        if(zid is None):
            zid = self.local
        s = '/{}/{}/plugins/yaks/backend/*'.format(
            Admin.PREFIX, zid)
        entries = self.ws.get(s)
        return list(map(
            lambda e: (e.get_path().split('/')[-1],
                       e.get_value().value), entries))

    def get_backend(self, beid, zid=None):
        '''
        Get backend's properties from the specified Zenoh router.

        :param beid: the Id of the backend.
        :param zid: the UUID of the Zenoh router. If ``None``, the local
            Zenoh router.
        '''
        if(zid is None):
            zid = self.local
        s = '/{}/{}/plugins/yaks/backend/{}'.format(
            Admin.PREFIX, zid, beid)
        entries = self.ws.get(s)
        if len(entries) > 0:
            return entries[0].get_value().value
        return None

    def remove_backend(self, beid, zid=None):
        '''
        Remove a backend from the specified Zenoh router.

        :param beid: the Id of the backend.
        :param zid: the UUID of the Zenoh router. If ``None``, the local
            Zenoh router.
        '''
        if(zid is None):
            zid = self.local
        path = '/{}/{}/plugins/yaks/backend/{}'.format(
            Admin.PREFIX, zid, beid)
        return self.ws.remove(path)

    def add_storage(self, stid, properties, beid=None, zid=None):
        '''
        Adds a storage in the specified Zenoh router, using the specified
        backend.

        :param stid: the Id of the storage.
        :param propertiers: some configuration for the storage.
        :param beid: the Id of the backend. If ``None``, a backend is
            automatically selected.
        :param zid: the UUID of the Zenoh router. If ``None``, the local
            Zenoh router.
        '''
        if(zid is None):
            zid = self.local
        if not beid:
            beid = 'auto'
        p = '/{}/{}/plugins/yaks/backend/{}/storage/{}'.format(
            Admin.PREFIX, zid, beid, stid)
        v = Value(properties, encoding=Encoding.PROPERTY)
        return self.ws.put(p, v)

    def get_storages(self, beid=None, zid=None):
        '''
        Get all the storages from the specified Zenoh router.

        :param beid: the Id of the backend. If ``None``, all backends.
        :param zid: the UUID of the Zenoh router. If ``None``, the local
            Zenoh router.
        '''
        if(zid is None):
            zid = self.local
        if not beid:
            beid = '*'
        s = '/{}/{}/plugins/yaks/backend/{}/storage/*'.format(
            Admin.PREFIX, zid, beid)
        entries = self.ws.get(s)
        return list(map(
            lambda e: (e.get_path().split('/')[-1],
                       e.get_value().value), entries))

    def get_storage(self, stid, zid=None):
        '''
        Get storage's properties from the specified Zenoh router.

        :param stid: the Id of the storage.
        :param zid: the UUID of the Zenoh router. If ``None``, the local
            Zenoh router.
        '''
        if(zid is None):
            zid = self.local
        s = '/{}/{}/plugins/yaks/backend/*/storage/{}'.format(
            Admin.PREFIX, zid, stid)
        entries = self.ws.get(s)
        if len(entries) > 0:
            return entries[0].get_value().value
        return None

    def remove_storage(self, stid, zid=None):
        '''
        Remove a backend from the specified Zenoh router.

        :param stid: the Id of the storage.
        :param zid: the UUID of the Zenoh router. If ``None``, the local
            Zenoh router.
        '''
        if(zid is None):
            zid = self.local
        s = '/{}/{}/plugins/yaks/backend/*/storage/{}'.format(
            Admin.PREFIX, zid, stid)
        entries = self.ws.get(s)
        if len(entries) > 0:
            p = entries[0].get_path()
            return self.ws.remove(p)
        return False