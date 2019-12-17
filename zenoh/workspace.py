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

from queue import Queue
from zenoh.encoding import Encoding, TranscodingFallback
from zenoh.path import Path
from zenoh.selector import Selector
from zenoh.value import Value, Change
from zenoh.entry import Entry
import zenoh.net
from zenoh.net import *


class Workspace(object):
    '''

    A Workspace to operate on Zenoh.

    '''

    def __init__(self, runtime, path, executor=None):
        self.rt = runtime
        self.path = Path.to_path(path)
        self.evals = []
        self.executor = executor

    def __to_absolute(self, path):
        if path.startswith('/'):
            return path
        else:
            return self.path.to_string() + '/' + path

    def put(self, path, value):
        '''

        Put a path/value into Zenoh.

        :param path: the Path. Can be absolute or relative to the workspace.
        :param value: the value.

        '''

        self.rt.write_data(
            self.__to_absolute(path),
            value.as_zn_payload(),
            Encoding.to_z_encoding(value.get_encoding()),
            zenoh.net.ZN_PUT)
        return True

    def update(self, path, value):
        '''

        Update a path/value into Zenoh.

        :param path: the Path. Can be absolute or relative to the workspace.
        :param value: a delta to be applied on the existing value.

        '''

        raise NotImplementedError("Update not yet implemented ...")

    def __isSelectorForSeries(self, selector):
        props = selector.get_properties()
        if props is None:
            return True
        for p in props.split(";"):
            if(p.startswith("starttime") or p.startswith("stoptime")):
                return True
        return False

    def get(self, selector, encoding=Encoding.RAW,
                fallback=TranscodingFallback.KEEP):
        '''

        Get a selection of path/value from Zenoh.

        :param selector: the selector expressing the selection.
        :returns: a list of entry.

        '''

        q = Queue()

        def callback(reply_value):
            q.put(reply_value)

        def contains_key(kvs, key):
            for (k, _) in kvs:
                if(k == key):
                    return True
            return False

        selector = Selector.to_selector(self.__to_absolute(selector))

        self.rt.query(
            selector.get_path(),
            selector.get_optional_part(),
            callback)
        resultsMap = {}
        reply = q.get()
        while(reply.kind != zenoh.net.ZN_REPLY_FINAL):
            if(reply.kind == zenoh.net.ZN_STORAGE_DATA
               or reply.kind == zenoh.net.ZN_EVAL_DATA):
                entry = Entry(reply.rname,
                              Value.from_zn_resource(reply.data, reply.info),
                              reply.info.tstamp)
                if reply.rname not in resultsMap:
                    resultsMap[reply.rname] = set()
                resultsMap[reply.rname].add(entry)
            reply = q.get()
        q.task_done()

        results = []
        if(self.__isSelectorForSeries(selector)):
            # return all entries
            for path, entrySet in resultsMap.items():
                for entry in sorted(entrySet):
                    results.append(entry)
        else:
            # return only the latest entry for each path
            for path, entrySet in resultsMap.items():
                entries = sorted(entrySet)
                results.append(entries[-1])

        return results

    def remove(self, path):
        '''

        Remove a path/value from Zenoh.

        :param path: the Path to be removed.
            Can be absolute or relative to the workspace.

        '''

        self.rt.write_data(
            self.__to_absolute(path),
            "".encode(),
            Encoding.ZN_RAW_ENC,
            zenoh.net.ZN_REMOVE)
        return True

    def subscribe(self, selector, listener):
        '''

        Subscribe to a selection of path/value from Zenoh.

        :param selector: the selector expressing the selection.
        :param listener: the Listener that will be called for each change of
            a path/value matching the selection.
        :returns: a subscription id.

        '''

        selector = self.__to_absolute(selector)
        if(listener is not None):
            def callback(rname, data, info):
                if self.executor is None:
                    listener([Change(
                        rname,
                        info.kind,
                        info.tstamp.time if info.tstamp is not None else None,
                        Value.from_zn_resource(data, info))])
                else:
                    self.executor.submit(listener, [Change(
                        rname,
                        info.kind,
                        info.tstamp.time if info.tstamp is not None else None,
                        Value.from_zn_resource(data, info))])
            return self.rt.declare_subscriber(
                selector,
                zenoh.net.SubscriberMode.push(),
                callback)
        else:
            def callback(rname, data, info):
                pass
            return self.rt.declare_subscriber(
                selector,
                zenoh.net.SubscriberMode.push(),
                callback)

    def unsubscribe(self, subscription_id):
        '''

        Unregisters a previous subscription.

        :param subscription_id: the subscription id to unregister.

        '''

        self.rt.undeclare_subscriber(subscription_id)
        return True

    def register_eval(self, path, callback):
        '''

        Registers an evaluation function under the provided path.

        :param path: the Path where the function can be triggered using
            :func:`~zenoh.workspace.Workspace.get`.
        :param callback: the evaluation function.

        '''

        path = self.__to_absolute(path)

        def query_handler(path_selector, content_selector, send_replies):
            def query_handler_p(path_selector, content_selector, send_replies):
                args = Selector.dict_from_properties(
                    Selector("{}?{}".format(path_selector, content_selector)))
                value = callback(path, args)
                info = zn_data_info_t()
                info.flags = 0x60
                info.encoding = Encoding.to_z_encoding(value.get_encoding())
                info.kind = ZN_PUT
                send_replies([(path, (value.as_zn_payload(), info))])
            if self.executor is None:
                query_handler_p(path_selector,
                                content_selector,
                                send_replies)
            else:
                self.executor.submit(query_handler_p,
                                     path_selector,
                                     content_selector,
                                     send_replies)

        zeval = self.rt.declare_eval(path,
                                     query_handler)

        self.evals.append((path, zeval))

    def unregister_eval(self, path):
        '''

        Unregister a previously registered evaluation function.

        :param path: the path where the function has been registered.

        '''

        path = self.__to_absolute(path)
        for (evalpath, zeval) in self.evals:
            if evalpath == path:
                self.rt.undeclare_eval(zeval)
        self.evals = [(evalpath, zeval) for (evalpath, zeval) in
                      self.evals if not evalpath == path]
        return True