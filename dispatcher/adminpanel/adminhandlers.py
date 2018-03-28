from tornado.web import RequestHandler
from sqlalchemy.ext import baked
from sqlalchemy import bindparam
from tornado_sqlalchemy import SessionMixin
from dispatcher.models import (Device,
                               DeviceType,
                               NurseDevice,
                               NurseDeviceType,
                               PatientDevice,
                               PatientDeviceType)
import json


class PanelHandler(RequestHandler, SessionMixin):
    def get(self):
        """Render the panel."""
        self.render('static/admin.html')


class DeviceHandler(RequestHandler, SessionMixin):
    def get(self):
        """Get all values for a given device"""
        uuid = self.get_argument('id', None)
        ret = None
        if uuid:
            ret = self._get(uuid)
            if 'device' in ret:
                self.set_status(200)
                self.write(ret)
                self.finish()
        else:
            ret = {
                'status': 'BAD',
                'code': 400,
                'error': 'No id provided'
            }
        self.set_status(400)
        self.write(ret)
        self.finish()

    def _get(self, id):
        device = None
        with self.make_session() as session:
            device = session.query(Device)\
                .filter(Device.id == id)\
                .first()

        if device:
            return {
                'status': 'OK',
                'device': device.serialize(),
                'code': 200,
            }
        else:
            return {
                'status': 'BAD',
                'code': 400,
            }

    def post(self):
        """POST - update the values for the given device id."""
        device_json = self.get_argument('device', None)
        device = None
        ret = None
        try:
            device = json.load(device_json)
            ret = self._post(device)
        except Exception as e:
            ret = {
                'status': 'FAILED',
                'code': 500,
                'error': 'ALL YOU BASE ARE BELONG TO US NOW',
            }
        self.set_status(ret['code'])
        self.write(ret)
        self.finish()

    def _post(self, device_json):
        devicetype_id = None
        location = None
        try:
            devicetype_id = device_json['devicetype']
            location = device_json['location']
        except Exception as e:
            return {
                'status': 'BAD',
                'code': 400,
                'error': 'Missing parameters; Require location and \
                device type'
            }
        patientdevice = None
        with self.make_session() as session:
            devicetype = session.query(DeviceType)\
                .filter(DeviceType.id == devicetype_id)\
                .first()
            if devicetype is None:
                return {
                    'status': 'BAD',
                    'code': 400,
                    'error': 'DeviceType doesn\'t exist'
                }
            patientdevice = PatientDevice(devicetype.id, location)
            session.add(patientdevice)
        if patientdevice:
            return {
                'status': 'OK',
                'code': 204,
                'device_id': patientdevice.id
            }
        else:
            return {
                'status': 'FAILED',
                'code': 500,
                'error': 'Must construct additional pylons & devs',
            }


class DevicesHandler(RequestHandler, SessionMixin):
    def get(self):
        """GET - returns all devices who's status satisfy the filter."""
        device_status = self.get_argument('devicestatus', None)
        used_by = self.get_argument('used_by', None)
        ret = None
        if device_status:
            ret = self._get(device_status, used_by)
        else:
            ret = {
                'status': 'BAD',
                'code': 400,
                'error': 'Missing parameter status'
            }
        self.set_status(ret['code'])
        self.write(ret)
        self.finish()

    def _get(self, status, used_by):
        devices = None
        with self.make_session() as session:
            baked_query = None
            if used_by is 'nurse':
                baked_query = session.query(NurseDevice)
            elif used_by is 'patient':
                baked_query = session.query(PatientDevice)
            else:
                baked_query = session.query(Device)
            devices = baked_query.filter(Device.status == status).all()
        if devices is not None:
            return {
                'status': 'OK',
                'code': 200,
                'devices': devices,
            }
        else:
            return {
                'status': 'FAILED',
                'code': 500,
                'error': 'pay me',
            }


class DeviceTypeHandler(RequestHandler, SessionMixin):
    def get(self):
        id = self.get_argument('id', None)
        ret = None
        if id:
            ret = self._get(id)
        else:
            ret = {
                'status': 'BAD',
                'code': 400,
                'error': 'No parameters',
            }
        self.set_status(ret['code'])
        self.write(ret)
        self.finish()

    def _get(self, id):
        device_type = None
        with self.make_session() as session:
            device_type = session.query(DeviceType)\
                .filter(DeviceType.id == id)\
                .first()
        if device_type:
            return {
                'status': 'OK',
                'code': 200,
                'device_type': device_type.serialize(),
            }
        else:
            return {
                'status': 'BAD',
                'code': 400,
            }

    def post(self):
        nurse_d_type_json = self.get_argument('patient_device_type', None)
        patient_d_type_json = self.get_argument('nurse_device_type', None)
        print('lol')
        ret = None
        if nurse_d_type_json and patient_d_type_json:
            ret = {
                'status': 'BAD',
                'code': 400,
                'error': 'Too many parameters',
            }
        if nurse_d_type_json is None and patient_d_type_json is None:
            ret = {
                'status': 'BAD',
                'code': 400,
                'error': 'No parameters',
            }
        if ret is None:
            used_by = 'patient'
            device_json = patient_d_type_json
            if nurse_d_type_json:
                used_by = 'nurse'
                device_json = nurse_d_type_json

            try:
                device_type = json.load(device_json)
                ret = self._post(device_type, used_by)
            except Exception as e:
                # TODO: Make this Json load specific
                ret = {
                    'status': 'BAD',
                    'code': 400,
                    'error': 'Invalid json',
                }
        self.set_status(ret['code'])
        self.write(ret)
        self.finish()

    def _post(self, device_type_d, used_by):
        if DeviceType.required_cols == set(device_type_d.keys()):
            device_type = None
            with self.make_session() as session:
                if used_by is 'nurse':
                    device_type = NurseDeviceType(
                        device_type_d['product_name'],
                        device_type_d['product_description'])
                else:
                    device_type = PatientDeviceType(
                        device_type_d['product_name'],
                        device_type_d['product_description'])
                session.add(device_type)
            if device_type:
                return {
                    'status': 'OK',
                    'code': 204
                }
            else:
                return {
                    'status': 'FAILED',
                    'code': 500,
                    'error': 'CSGames was an inside job',
                }
        else:
            return {
                'status': 'BAD',
                'code': 400,
                'error': 'Missing parameters',
            }


class DeviceTypesHandler(RequestHandler, SessionMixin):
    def get(self):
        id = self.get_argument('used_by', None)
        ret = None
        if id:
            ret = self._get(id)
        else:
            ret = {
                'status': 'BAD',
                'code': 400,
                'error': 'No parameters',
            }
        self.set_status(ret['code'])
        self.write(ret)
        self.finish()

    def _get(self, used_by):
        device_types = None
        with self.make_session() as session:
            if used_by is 'nurse':
                device_types = session.query(NurseDeviceType).all()
            elif used_by is 'patient':
                device_types = session.query(PatientDeviceType).all()
            else:
                device_types = session.query(DeviceType).all()
        if device_types is not None:
            return {
                'status': 'OK',
                'code': 200,
                'device_types': device_types,
            }
        else:
            return {
                'status': 'FAILED',
                'code': 500,
                'error': 'pay me IN BITCOIN',
            }


class CredentialsHandler(RequestHandler, SessionMixin):
    def get(self):
        pass
