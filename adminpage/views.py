from django.shortcuts import render

# Create your views here.
from codex.baseerror import *
from codex.baseview import APIView

from django.contrib import auth
from django.contrib.auth import authenticate
from django.core import serializers

from wechat.models import Activity, Ticket
from wechat.views import CustomWeChatView
from codex.baseerror import BaseError

import json, datetime, time, os, uuid

class AdminLogin(APIView):

    def get(self):
        if self.request.user.is_authenticated():
            return None
        else:
            raise ValidateError('')

    def post(self):
        self.check_input('username', 'password')
        usn = self.input['username']
        pwd = self.input['password']
        user = authenticate(username=usn, password=pwd)
        if user is not None and user.is_active:
            auth.login(self.request, user)
            return None
        raise ValidateError('')

class AdminLogout(APIView):

    def post(self):
        auth.logout(self.request)
        return None

class AdminActivityList(APIView):

    def stringToTimeStamp(self, date_str):
        d = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        t = d.timetuple()
        timeStamp = int(time.mktime(t))
        timeStamp = float(str(timeStamp) + str("%06d" % d.microsecond)) / 1000000
        return int(timeStamp)

    def formatActivityList(self, act_json_list):
        res_list = []
        for line in act_json_list:
            tmp_dict = {}
            fields = line['fields']
            tmp_dict['id'] = line['pk']
            tmp_dict['name'] = fields['name']
            tmp_dict['description'] = fields['description']
            tmp_time = fields['start_time'].replace("T", " ").replace("Z", "")
            tmp_dict['startTime'] = self.stringToTimeStamp(tmp_time)
            tmp_time = fields['end_time'].replace("T", " ").replace("Z", "")
            tmp_dict['endTime'] = self.stringToTimeStamp(tmp_time)
            tmp_dict['place'] = fields['place']
            tmp_time = fields['book_start'].replace("T", " ").replace("Z", "")
            tmp_dict['bookStart'] = self.stringToTimeStamp(tmp_time)
            tmp_time = fields['book_end'].replace("T", " ").replace("Z", "")
            tmp_dict['bookEnd'] = self.stringToTimeStamp(tmp_time)
            tmp_dict['currentTime'] = int(time.time())
            tmp_dict['status'] = fields['status']
            res_list.append(tmp_dict)
        return res_list

    def get(self):
        activity_json = json.loads(serializers.serialize("json", Activity.objects.all()))
        activity = self.formatActivityList(activity_json)
        return activity

class AdminActivityDelete(APIView):

    def post(self):
        self.check_input('id')
        del_id = self.input["id"]
        del_act = Activity.objects.get(id=del_id)
        if del_act is not None:
            del_act.delete()
            return None
        else:
            raise InputError('')

class AdminActivityCreate(APIView):

    def add8Hours(self, timestr):
        date_time = time.strptime(timestr,"%Y-%m-%dT%H:%M:%S.%fZ")
        time_stamp = int(time.mktime(date_time))
        time_stamp += 8 * 60 * 60
        time_tuple = time.localtime(time_stamp)
        date_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', time_tuple)
        return date_time

    def post(self):
        self.check_input('name', 'key', 'place' , 'description', 'startTime', 'endTime', 'bookStart'
                         , 'bookEnd', 'totalTickets', 'status', 'picUrl')
        act_info = self.input
        new_act = Activity(name=act_info["name"], key=act_info["key"], place=act_info["place"],
                           description=act_info["description"], start_time=self.add8Hours(act_info["startTime"]),
                           end_time=self.add8Hours(act_info["endTime"]), book_start=self.add8Hours(act_info["bookStart"]),
                           book_end=self.add8Hours(act_info["bookEnd"]), total_tickets=act_info["totalTickets"],
                           status=act_info["status"], pic_url=act_info["picUrl"],
                           remain_tickets=act_info["totalTickets"])
        new_act.save()
        id = new_act.id
        return id

class AdminImageUpload(APIView):

    def post(self):
        self.check_input('image')
        img = self.input['image'][0]
        img_name = './media/img/%s' % (str(uuid.uuid1()) + '-' + img.name)
        with open(img_name, 'wb') as f:
            for fimg in img.chunks():
                f.write(fimg)
        img_url = self.request.get_host() + self.request.path + img_name.strip('.')
        return img_url

class AdminActivityDetail(APIView):

    def add8Hours(self, timestr):
        date_time = time.strptime(timestr,"%Y-%m-%dT%H:%M:%S.%fZ")
        time_stamp = int(time.mktime(date_time))
        time_stamp += 8 * 60 * 60
        time_tuple = time.localtime(time_stamp)
        date_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', time_tuple)
        return date_time

    def stringToTimeStamp(self, date_str):
        d = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        t = d.timetuple()
        timeStamp = int(time.mktime(t))
        timeStamp = float(str(timeStamp) + str("%06d" % d.microsecond)) / 1000000
        return int(timeStamp)

    def formatActivityDetail(self, act_json):
        fields = act_json[0]['fields']
        tmp_dict = {}
        tmp_dict['name'] = fields['name']
        tmp_dict['key'] = fields['key']
        tmp_dict['description'] = fields['description']
        tmp_time = fields['start_time'].replace("T", " ").replace("Z", "")
        tmp_dict['startTime'] = self.stringToTimeStamp(tmp_time)
        tmp_time = fields['end_time'].replace("T", " ").replace("Z", "")
        tmp_dict['endTime'] = self.stringToTimeStamp(tmp_time)
        tmp_dict['place'] = fields['place']
        tmp_time = fields['book_start'].replace("T", " ").replace("Z", "")
        tmp_dict['bookStart'] = self.stringToTimeStamp(tmp_time)
        tmp_time = fields['book_end'].replace("T", " ").replace("Z", "")
        tmp_dict['bookEnd'] = self.stringToTimeStamp(tmp_time)
        tmp_dict['totalTickets'] = fields['total_tickets']
        tmp_dict['picUrl'] = fields['pic_url']
        tmp_dict['bookedTickets'] = fields['total_tickets'] - fields['remain_tickets']
        tmp_dict['usedTickets'] = 0
        tmp_dict['currentTime'] = int(time.time())
        tmp_dict['status'] = fields['status']
        return tmp_dict

    def get(self):
        self.check_input('id')
        act_id = self.input['id']
        detail_queryset = Activity.objects.filter(id=act_id)
        detail_json = json.loads(serializers.serialize("json", detail_queryset))
        detail = self.formatActivityDetail(detail_json)
        return detail

    def post(self):
        self.check_input('id', 'name', 'place', 'description', 'picUrl', 'startTime', 'endTime', 'bookStart',
                         'bookEnd', 'totalTickets', 'status')
        new_act_info = self.input
        act_id = new_act_info['id']
        current = int(time.time())
        try:
            act = Activity.objects.get(id=act_id)
        except:
            raise LogicError('no activity')
        else:
            if act.status == 0:
                act.name = new_act_info['name']
                act.place = new_act_info['place']
            act.description = new_act_info['description']
            act.pic_url = new_act_info['picUrl']
            if current < self.stringToTimeStamp(act.end_time):
                act.start_time = self.add8Hours(new_act_info['startTime'])
                act.end_time = self.add8Hours(new_act_info['endTime'])
            if act.status == 0:
                act.book_start = self.add8Hours(new_act_info['bookStart'])
                act.status = new_act_info['status']
            if current < self.stringToTimeStamp(act.start_time):
                act.book_end = self.add8Hours(new_act_info['bookEnd'])
            if current < self.stringToTimeStamp(act.book_start):
                act.total_tickets = new_act_info['totalTickets']
            act.save()
        return None

class AdminActivityMenu(APIView):

    def get(self):
        res = []
        act = Activity.objects.all()
        current_stamp = int(time.time())
        for line in act:
            start_stamp = time.mktime(line.book_start.timetuple())
            end_stamp = time.mktime(line.book_end.timetuple())
            if start_stamp < current_stamp and current_stamp < end_stamp:
                tmp_dict = {}
                tmp_dict['id'] = line.id
                tmp_dict['name'] = line.name
                tmp_dict['menuIndex'] = 0
                res.append(tmp_dict)
        return res

    def post(self):
        if isinstance(self.input, list) == False:
            raise InputError('')
        input_list = self.input
        act_list = []
        for update_id in input_list:
            act = Activity.objects.get(id=update_id)
            act_list.append(act)
        CustomWeChatView.update_menu(act_list)
        return None

class AdminActivityCheckin(APIView):

    def datetimeToStamp(self, date_time):
        return int(time.mktime(date_time.timetuple()))

    def post(self):
        self.check_input('actId')
        # 活动是否存在
        try:
            act = Activity.objects.get(id=int(self.input['actId']))
        except:
            raise LogicError('activity not found')
        else:
            act_start = self.datetimeToStamp(act.start_time)
            act_end = self.datetimeToStamp(act.end_time)
            current = int(time.time())
            if current < act_start or current > act_end:
                raise LogicError('not activity time')
        # 输入是否合法
        try:
            if 'ticket' in self.input:
                ticket = Ticket.objects.get(unique_id=self.input['ticket'])
            elif 'studentId' in self.input:
                ticket = Ticket.objects.get(student_id=self.input['studentId'])
            else:
                raise InputError('input error')
        except:
            raise LogicError('ticket not found')
        else:
            if ticket.status != Ticket.STATUS_VALID:
                raise LogicError('invalid ticket')
            ticket.status = Ticket.STATUS_USED
            ticket.save()
return {'ticket': ticket.unique_id, 'studentId': ticket.student_id}
