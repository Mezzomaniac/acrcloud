#! /usr/bin/env python3
# acrcloud.py - interface with ACRCloud's music recognition web API

import base64
import hashlib
import hmac
import json
import time

import requests

class ACRCloudConsole:
    """ACRCloud's web API console for remotely managing projects.

    Usage: ACRCloudConsole(account_access_key, account_access_secret)

    Get account_access_key and account_access_secret by creating an account on acrcloud.com

    See www.acrcloud.com/docs/audio-fingerprinting-api/console-api/projects"""

    def __init__(self, account_access_key: str, account_access_secret: bytes):
        """Get account_access_key and account_access_secret by creating an account on acrcloud.com"""

        self.access_key = account_access_key
        self.access_secret = account_access_secret
        self.host = 'api.acrcloud.com'
        self.signature_version = '1'

    def _sign(self, string_to_sign: str):
        """Helper function.

        See www.acrcloud.com/docs/audio-fingerprinting-api/console-api/signing-requests"""

        return base64.b64encode(
            hmac.new(
                self.access_secret, string_to_sign.encode(), digestmod=hashlib.sha1)
            .digest())

    def _headers(self, signature, timestamp: str) -> dict:
        """Helper function."""

        return {'access-key': self.access_key, 'signature-version': self.signature_version, 'signature': signature, 'timestamp': timestamp}

    def add_project(self, project_name: str, type_: str='BM-ACRC', buckets: list=None, audio_type: int=2, external_id: str='', region: str='ap-southeast-1') -> str:
        """Add a project.

        type_ (str) is project type, which can be:
            AVR: Audio & Video Recognition
            BM-ACRC: Broadcast Monitoring (default)
            LCD: Live Channel Detection
            HR: Hybrid Recognition

        buckets (list) gets converted to json [{"id":id, "name":name}]. Name is "ACRCloud Music" (default) or "ACRCloud Chinese TV"

        audio_type (int) is 1 for recorded audio or 2 for line-in audio (default)

        external_id (str) contains 0 or more of "deezer, itunes, spotify"

        region (str) can be:
            Asia (Singapore): "ap-southeast-1" (default)
            Europe (Ireland): "eu-west-1"

        Response is json string with keys "access_key", "access_secret", "name", "region", "created_at"

        See www.acrcloud.com/docs/audio-fingerprinting-api/console-api/projects"""

        if buckets is None:
            buckets = [{'name': 'ACRCloud Music'}]

        http_method = 'POST'
        uri = '/v1/projects'
        timestamp = str(time.time())

        string_to_sign = '\n'.join((http_method, uri, self.access_key, self.signature_version, timestamp))
        signature = self._sign(string_to_sign)
        headers = self._headers(signature, timestamp)
        data = {'name': project_name, 'region': region, 'type': type_, 'buckets': json.dumps(buckets), 'audio_type': audio_type, 'external_id': external_id}

        requrl = 'https://{}{}'.format(self.host, uri)
        response = requests.post(requrl, data=data, headers=headers, verify=True)
        response.encoding = 'utf-8'
        return response.text

    def update_project(self, project_name: str, buckets: list=None) -> str:
        """Update a project's buckets.

        buckets (list) gets converted to json [{"id":id, "name":name}]. Name is "ACRCloud Music" (default) or "ACRCloud Chinese TV"

        Response is json string with keys "access_key", "access_secret", "name", "region", "update_at"

        See www.acrcloud.com/docs/audio-fingerprinting-api/console-api/projects"""

        if buckets is None:
            buckets = [{'name': 'ACRCloud Music'}]
        
        http_method = 'POST'  # Or should this be PUT?
        uri = '/v1/projects/' + project_name
        timestamp = str(time.time())

        string_to_sign = '\n'.join((http_method, uri, self.access_key, self.signature_version, timestamp))
        signature = self._sign(string_to_sign)
        headers = self._headers(signature, timestamp)
        data = {'buckets': json.dumps(buckets)}

        requrl = 'https://{}{}'.format(self.host, uri)
        response = requests.post(requrl, data=data, headers=headers, verify=True)  # Or should this be requests.put?
        response.encoding = 'utf-8'
        return response.text

    def delete_project(self, project_name: str) -> str:
        """Delete a project.

        See www.acrcloud.com/docs/audio-fingerprinting-api/console-api/projects"""

        http_method = 'DELETE'
        uri = '/v1/projects/' + project_name
        timestamp = str(time.time())

        string_to_sign = '\n'.join((http_method, uri, self.access_key, self.signature_version, timestamp))
        signature = self._sign(string_to_sign)
        headers = self._headers(signature, timestamp)
        data = {'name': project_name}

        requrl = 'https://{}{}'.format(self.host, uri)
        response = requests.delete(requrl, data=data, headers=headers, verify=True)
        response.encoding = 'utf-8'
        return response.text

    def get_project(self, project_name: str) -> str:
        """Get a project's details(?)

        Not documented in ACRCloud docs."""

        http_method = 'GET'
        uri = '/v1/projects/' + project_name
        timestamp = str(time.time())

        string_to_sign = '\n'.join((http_method, uri, self.access_key, self.signature_version, timestamp))
        signature = self._sign(string_to_sign)
        headers = self._headers(signature, timestamp)

        requrl = 'https://{}{}'.format(self.host, uri)
        response = requests.get(requrl, headers=headers, verify=True)
        response.encoding = 'utf-8'
        return response.text

    def list_projects(self):
        """Get a list of projects.

        Not documented in ACRCloud docs."""

        http_method = 'GET'
        uri = '/v1/projects'
        timestamp = str(time.time())

        string_to_sign = '\n'.join((http_method, uri, self.access_key, self.signature_version, timestamp))
        signature = self._sign(string_to_sign)
        headers = self._headers(signature, timestamp)

        requrl = 'https://{}{}'.format(self.host, uri)
        response = requests.get(requrl, headers=headers, verify=True)
        response.encoding = 'utf-8'
        return response.text

    def add_monitor(self, project_name: str, stream_name: str, url: str, region: str='ap-southeast-1', realtime: int=1, record: int=0) -> str:
        """Add a stream to a project for monitoring.

        url (str) is a radio station url with an appropriate media file suffix

        region (str) can be:
            Asia (Singapore): "ap-southeast-1" (default)
            Europe (Ireland): "eu-west-1"
            America: "us-west-2"
            Local: "local"

        realtime (int) can be:
            1: on, for raw results within 1 min (default)
            0: off, for refined results within 5-10 mins

        record (int) can be 0 (default) or 1  # What does this mean?

        Response is json string with keys "url", "state", "interval", "rec_length", "rec_timeout", "stream_name", "id", "realtime", "record"

        See https://www.acrcloud.com/docs/audio-fingerprinting-api/console-api/monitors/"""

        http_method = 'POST'
        uri = '/v1/monitor-streams'
        timestamp = str(time.time())

        string_to_sign = '\n'.join((http_method, uri, self.access_key, self.signature_version, timestamp))
        signature = self._sign(string_to_sign)
        headers = self._headers(signature, timestamp)
        data = {'project_name': project_name, 'stream_name': stream_name, 'url': url, 'region': region, 'realtime': realtime, 'record': record}

        requrl = 'https://{}{}'.format(self.host, uri)
        response = requests.post(requrl, data=data, headers=headers, verify=True)
        response.encoding = 'utf-8'
        return response.text

    def update_monitor(self, stream_id: str, stream_name: str, url: str, region: str='ap-southeast-1', realtime: int=1, record: int=0) -> str:
        """Update a project stream.

        url (str) is a radio station url with an appropriate media file suffix

        region (str) can be:
            Asia (Singapore): "ap-southeast-1" (default)
            Europe (Ireland): "eu-west-1"
            America: "us-west-2"
            Local: "local"

        realtime (int) can be:
            1: on, for raw results within 1 min (default)
            0: off, for refined results within 5-10 mins

        record (int) can be 0 or 1  # What does this mean?

        Response is json string with keys "url", "state", "interval", "rec_length", "rec_timeout", "stream_name", "id", "region", "realtime", "record"

        See https://www.acrcloud.com/docs/audio-fingerprinting-api/console-api/monitors/"""

        http_method = 'PUT'
        uri = '/v1/monitor-streams/' + stream_id
        timestamp = str(time.time())

        string_to_sign = '\n'.join((http_method, uri, self.access_key, self.signature_version, timestamp))
        signature = self._sign(string_to_sign)
        headers = self._headers(signature, timestamp)
        data = {'stream_name': stream_name, 'url': url, 'region': region, 'realtime': realtime, 'record': record}

        requrl = 'https://{}{}'.format(self.host, uri)
        response = requests.put(requrl, data=data, headers=headers, verify=True)
        response.encoding = 'utf-8'
        return response.text

    def get_all_monitors(self, project_name: str) -> str:
        """Get a list of all monitors on the project.

        Response is json string with the following keys and sub-keys:
            "items": for each item: "id", "url", "state", "interval", "rec_length", "rec_timeout", "stream_name"
            "_links": "self": "href"
            "_meta": "totalCount", "pageCount", "currentPage", "perPage"

        See https://www.acrcloud.com/docs/audio-fingerprinting-api/console-api/monitors/"""

        http_method = 'GET'
        uri = '/v1/monitor-streams'
        timestamp = str(time.time())

        string_to_sign = '\n'.join((http_method, uri, self.access_key, self.signature_version, timestamp))
        signature = self._sign(string_to_sign)
        headers = self._headers(signature, timestamp)
        data = {'project_name': project_name}

        requrl = 'https://{}{}'.format(self.host, uri)
        response = requests.put(requrl, data=data, headers=headers, verify=True)
        response.encoding = 'utf-8'
        return response.text

    def get_monitor(self, stream_id: str) -> str:
        """Get a monitor's details.

        Response is json string with keys "id", "url", "state", "interval", "rec_length", "rec_timeout", "stream_name"

        See https://www.acrcloud.com/docs/audio-fingerprinting-api/console-api/monitors/"""

        http_method = 'GET'
        uri = '/v1/monitor-streams/' + stream_id
        timestamp = str(time.time())

        string_to_sign = '\n'.join((http_method, uri, self.access_key, self.signature_version, timestamp))
        signature = self._sign(string_to_sign)
        headers = self._headers(signature, timestamp)

        requrl = 'https://{}{}'.format(self.host, uri)
        response = requests.get(requrl, headers=headers, verify=True)
        response.encoding = 'utf-8'
        return response.text

    def delete_monitor(self, stream_id: str) -> str:
        """Delete a monitor.

        See https://www.acrcloud.com/docs/audio-fingerprinting-api/console-api/monitors/"""

        http_method = 'DELETE'
        uri = '/v1/monitor-streams/' + stream_id
        timestamp = str(time.time())

        string_to_sign = '\n'.join((http_method, uri, self.access_key, self.signature_version, timestamp))
        signature = self._sign(string_to_sign)
        headers = self._headers(signature, timestamp)

        requrl = 'https://{}{}'.format(self.host, uri)
        response = requests.delete(requrl, headers=headers, verify=True)
        response.encoding = 'utf-8'
        return response.text

    def action_monitor(self, stream_id: str, action: str) -> str:
        """Pause or restart a monitor.

        action (str) is "pause" or "restart"

        Response is json string {"message": "success"} if successful

        See https://www.acrcloud.com/docs/audio-fingerprinting-api/console-api/monitors/"""

        http_method = 'PUT'
        uri = '/v1/monitor-streams/{}/{}'.format(stream_id, action)
        timestamp = str(time.time())

        string_to_sign = '\n'.join((http_method, uri, self.access_key, self.signature_version, timestamp))
        signature = self._sign(string_to_sign)
        headers = self._headers(signature, timestamp)

        requrl = 'https://{}{}'.format(self.host, uri)
        response = requests.put(requrl, headers=headers, verify=True)
        response.encoding = 'utf-8'
        return response.text

    def pause_monitor(self, stream_id: str) -> str:
        """Pause a monitor.

        Convenience alias for self.action_monitor(stream_id, "pause")

        Response is json string {"message": "success"} if successful."""

        return self.action_monitor(stream_id, 'pause')

    def restart_monitor(self, stream_id: str) -> str:
        """Restart a monitor.

        Convenience alias for self.action_monitor(stream_id, "restart")

        Response is json string {"message": "success"} if successful."""

        return self.action_monitor(stream_id, 'restart')


class ACRCloudStreamMonitor:
    """ACRCloud's web API for stream monitor results.

    Usage: ACRCloudStreamMonitor(project_access_key, stream_id)

    Get account_access_key and account_access_secret by creating an account on acrcloud.com

    See www.acrcloud.com/docs/audio-fingerprinting-api/monitoring-api/"""

    def __init__(self, project_access_key: str, stream_id: str):
        """Get project_access_key from Broadcast Monitoring project page on acrcloud.com.
        Click project name on Stream Management page to find stream_id."""

        self.access_key = project_access_key
        self.stream_id = stream_id

    def last_results(self) -> str:
        """Gets the last result that the monitor service detects from the stream.

        See www.acrcloud.com/docs/audio-fingerprinting-api/monitoring-api/

        Response is JSON as described at www.acrcloud.com/docs/acrcloud/metadata/music/"""

        requrl = 'https://api.acrcloud.com/v1/monitor-streams/{}/results?access_key={}'\
            .format(self.stream_id, self.access_key)
        response = requests.get(requrl)
        response.encoding = 'utf-8'
        return response.text

    def current_results(self) -> str:
        """Gets the last result that displayed “no result”, when it doesn’t detect any result.

        See www.acrcloud.com/docs/audio-fingerprinting-api/monitoring-api/

        Response is JSON as described at www.acrcloud.com/docs/acrcloud/metadata/music/"""

        requrl = 'https://api.acrcloud.com/v1/monitor-streams/{}/results?access_key={}&type=current'\
            .format(self.stream_id, self.access_key)
        response = requests.get(requrl)
        response.encoding = 'utf-8'
        return response.text

    def multiple_last_results(self, limit: int) -> str:
        """Gets multiple last results, from the last 1 result to the last 100 results.

        See www.acrcloud.com/docs/audio-fingerprinting-api/monitoring-api/

        Response is JSON as described at www.acrcloud.com/docs/acrcloud/metadata/music/"""

        requrl = 'https://api.acrcloud.com/v1/monitor-streams/{}/results?access_key={}&limit={}'\
            .format(self.stream_id, self.access_key, limit)
        response = requests.get(requrl)
        response.encoding = 'utf-8'
        return response.text

    def day_results(self, date: str) -> str:
        """Gets full day results in last 30 days.

        date is in YYYYMMDD format

        Timezone is UTC.

        If the date is current day then the results are till the moment of the request.

        See www.acrcloud.com/docs/audio-fingerprinting-api/monitoring-api/

        Response is JSON as described at www.acrcloud.com/docs/acrcloud/metadata/music/"""

        requrl = 'https://api.acrcloud.com/v1/monitor-streams/{}/results?access_key={}&date={}'\
            .format(self.stream_id, self.access_key, date)
        response = requests.get(requrl)
        response.encoding = 'utf-8'
        return response.text

    def month_results(self, month: str):
        """Gets full month monitoring results of any past month.

        month is in YYYYMM format

        downloads a .zip file

        See www.acrcloud.com/docs/audio-fingerprinting-api/monitoring-api/"""

        requrl = 'https://monitoring-result.acrcloud.com/{}/{}/{}.zip'\
            .format(self.access_key, self.stream_id, month)
        response = requests.get(requrl)
        return response  # Or should something else be returned because it's a file?

    def period_results(self, begin_time: str, end_time: str='') -> str:
        """Gets monitoring results in a certain period of the last 24 hours.

        begin_time and end_time are in YYYYMMDDHHMMSS format

        end_time is optional - defaults to now

        Timezone is UTC

        See www.acrcloud.com/docs/audio-fingerprinting-api/monitoring-api/

        Response is JSON as described at www.acrcloud.com/docs/acrcloud/metadata/music/"""

        requrl = 'https://api.acrcloud.com/v1/monitor-streams/{}/results?access_key={}&begin_time={}&end_time={}'\
            .format(self.stream_id, self.access_key, begin_time, end_time)
        response = requests.get(requrl)
        response.encoding = 'utf-8'
        return response.text

if __name__ == '__main__':
    account_access_key = '41722687922d4eb9'
    account_access_secret = b'542e4b0d4a26f5aedbd527d17ebf968e'
    project_access_key = '6766d2e7b2cb858d9405bb94b991369b'
    stream_id_96fm = '11396'
    stream_id_mix945 = '11551'
    console = ACRCloudConsole(account_access_key, account_access_secret)
    monitor_96fm = ACRCloudStreamMonitor(project_access_key, stream_id_96fm)
    monitor_mix945 = ACRCloudStreamMonitor(project_access_key, stream_id_mix945)
    print(console.get_monitor(monitor_96fm.stream_id))
    print(console.get_monitor(monitor_mix945.stream_id))
