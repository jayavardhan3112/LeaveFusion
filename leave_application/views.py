from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import HttpResponse, Http404, JsonResponse
from leave_application.forms import (FacultyLeaveForm,
                                     StaffLeaveForm,
                                     StudentLeaveForm,)

from user_app.models import Administration
from leave_application.models import Leave, CurrentLeaveRequest, LeaveRequest
from django.contrib.auth.models import User
from leave_application.helpers import FormData, get_object_or_none

class ApplyLeave(View):
    """
        A Class Based View which handles user applying for leave
    """
    def get(self, request):
        """
            view to handle get request to /leave/apply
        """
        form = self.get_form(request)
        return render(request, 'leave_application/apply_for_leave.html', {'form': form, 'title': 'Leave', 'action':'Apply'})

    def post(self, request):
        """
            view to handle post request to /leave/apply
        """
        form = self.get_form(request)
        # form2 = FacultyLeaveForm(request.POST, user=request.user)
        # print(form2.is_valid())
        # print(form2.errors)

        if form.is_valid():

            acad_done = False if form.cleaned_data.get('acad_rep', False) else True
            admin_done = False if form.cleaned_data.get('admin_rep', False) else True
            academic_replacement = get_object_or_none(User, username=form.cleaned_data.get('acad_rep'))
            administrative_replacement = get_object_or_none(User,
                                                            username=form.cleaned_data.get('admin_rep'))
            try:
                leave_obj = Leave.objects.create(
                    applicant = request.user,
                    type_of_leave = form.cleaned_data['type_of_leave'],
                    academic_replacement = academic_replacement,
                    administrative_replacement = administrative_replacement,
                    purpose = form.cleaned_data['purpose'],
                    acad_done = acad_done,
                    admin_done = admin_done,
                    leave_address = form.cleaned_data.get('leave_address', ''),
                    start_date = form.cleaned_data['start_date'],
                    end_date = form.cleaned_data['end_date'],
                )

            except Exception as e:
                return render(request,
                              'leave_application/apply_for_leave.html',
                              {'form': form, 'message': 'Failed'})
            return render(request, 'leave_application/apply_for_leave', {'message': 'success', 'title': 'Leave', 'action':'Apply'})

        else:
            return render(request, 'leave_application/apply_for_leave.html', {'form': form, 'title': 'Leave', 'action':'Apply'})

    def get_user_type(self, request):
        return request.user.extrainfo.user_type

    def get_form(self, request):

        user_type = self.get_user_type(request)

        if user_type == 'faculty':
            form = self.get_form_object(FacultyLeaveForm, request)

        elif user_type == 'staff':
            form = self.get_form_object(StaffLeaveForm, request)
        else:
            form = self.get_form_object(StudentLeaveForm, request)

        return form

    def get_form_object(self, cls, request):

        if request.method == 'GET':
            return cls(initial={}, user=request.user)
        else:
            return cls(request.POST, user=request.user)

class ProcessRequest(View):

    def get(self, request, id):

        leave_request = get_object_or_404(CurrentLeaveRequest, id=id)
        type_of_leave = leave_request.leave.type_of_leave

        do = request.GET.get('do')
        remark = request.GET.get('remark', '')

        sanc_auth = leave_request.applicant.extrainfo.department.sanctioning_authority
        sanc_officer = leave_request.applicant.extrainfo.department.sanctioning_officer
        designation = request.user.extrainfo.designation
        for_replacement = leave_request.permission == 'academic' \
                    or leave_request.permission == 'admin'
        if do == 'accept':
            if leave_request.permission == 'academic':
                if leave_request.leave.academic_replacement == request.user:
                    leave_request = self.create_leave_request(leave_request, False, accept=True, remark=remark)
                    leave_request.leave.acad_done = True
                else:
                    return JsonResponse({'message': 'Not allowed', 'type': 'error'}, status=200)

            elif leave_request.permission == 'admin':
                if leave_request.leave.administrative_replacement == request.user:
                    leave_request = self.create_leave_request(leave_request, False, accept=True, remark=remark)
                    leave_request.leave.admin_done = True
                else:
                    return JsonResponse({'message': 'Not allowed', 'type': 'error'}, status=200)

            elif leave_request.permission == 'sanc_auth':

                if sanc_auth == designation and type_of_leave in ['casual', 'restricted']:

                    leave_request = self.create_leave_request(leave_request, True, accept=True, remark=remark)
                    leave_request.leave.status = 'accepted'
                    leave_request.leave.save()

                else:
                    return JsonResponse({'message': 'Not allowed', 'type': 'error'}, status=200)

            elif leave_request.permission == 'sanc_officer':

                if sanc_officer == designation:

                    leave_request = self.create_leave_request(leave_request, True, accept=True, remark=remark)
                    leave_request.leave.status = 'accepted'
                    leave_request.leave.save()

                else:
                    return JsonResponse({'message': 'Not allowed', 'type': 'error'}, status=200)

            else:
                return JsonResponse({'message': 'Not allowed', 'type': 'error'}, status=200)

            leave_request.leave.save()
            if for_replacement and leave_request.leave.acad_done \
               and leave_request.leave.admin_done:

                # if type_of_leave in ['casual', 'restricted']:
                #     next_user = Administration.objects.filter(position=sanc_auth).first().administrator
                #     next_position = sanc_auth
                # else:
                #     next_user = Administration.objects.filter(position=sanc_officer).first().administrator
                #     next_position = sanc_officer
                next_user = Administration.objects.filter(position=sanc_auth).first().administrator
                CurrentLeaveRequest.objects.create(
                    applicant = leave_request.applicant,
                    requested_from = next_user,
                    position = sanc_auth,
                    leave = leave_request.leave,
                    permission = 'sanc_auth',
                )

        elif do == 'reject':

            if sanc_auth == designation and type_of_leave not in ['casual', 'restricted']:
                raise Http404

            if sanc_auth == sanc_officer and designation == sanc_auth:
                self.create_leave_request(leave_request, True, accept=False, remark=remark)

            elif designation in [sanc_auth, sanc_officer]:
                leave_request = self.create_leave_request(leave_request,
                                                          True, accept=False,
                                                          remark=remark)
            elif leave_request.requested_from == request.user:
                leaves_data = leave_request.leave.cur_requests
                for leave in leaves_data:
                    self.create_leave_request(leave, False, accept=False, remark=remark)

            else:
                return JsonResponse({'message':'Not Allowed', 'type': 'error'}, status=200)

            leave_request.leave.status = 'rejected'
            leave_request.leave.save()

        elif do == 'forward':
            if sanc_auth == designation and type_of_leave not in ['casual', 'restricted']:
                leave_request = self.create_leave_request(leave_request, False, accept=True, remark=remark)
                sanc_officer_user = Administration.objects.filter(position=sanc_officer).first().administrator
                CurrentLeaveRequest.objects.create(
                    applicant=leave_request.applicant,
                    requested_from = sanc_officer_user,
                    position = sanc_officer,
                    leave = leave_request.leave,
                    permission = 'sanc_officer',
                )

            else:
                return JsonResponse({'message': 'Not allowed', 'type': 'error'}, status=200)

        else:
            raise Http404

        return JsonResponse({'message': 'Operation Successful'}, status=200)

    def create_leave_request(self, cur_leave_request, final, accept=False, remark=''):
        leave_request = LeaveRequest.objects.create(
            leave = cur_leave_request.leave,
            applicant = cur_leave_request.applicant,
            requested_from = cur_leave_request.requested_from,
            remark = remark,
            position = cur_leave_request.position,
            status = accept,
        )

        if not accept and final:
            cur_leave_request.leave.status = 'rejected'
        elif final:
            cur_leave_request.leave.status = 'accepted'

        cur_leave_request.delete()
        return leave_request

class GetApplications(View):

    def get(self, request):

        request_list = map(lambda x: FormData(request, x),
                           CurrentLeaveRequest.objects.filter(requested_from=request.user))
        return render(request, 'leave_application/get_requests.html', {'requests': request_list})


"""

def get(self):
    if do=='accept':
                    # if sanc_auth == sanc_officer and designation == sanc_auth:
                    #     self.create_leave_request(leave_request, True, accept=True, remark=remark)
                    #
                    # elif sanc_auth == designation:
                    #
                    #     if type_of_leave not in ['casual', 'restricted']:
                    #         raise Http404
                    #
                    #         leave_request = self.create_leave_request(leave_request,
                    #         True, accept=True,
                    #         remark=remark)
                    #
                    #     elif sanc_officer == designation:
                    #
                    #         self.create_leave_request(leave_request, True, accept=True, remark=remark)
                    #
                    #     elif designation == leave_request.position:
                    #         leave_request = self.create_leave_request(leave_request, False, accept=True, remark=remark)
                    #         if leave_request.leave.academic_replacement == leave_request.requested_from:
                    #             leave_request.leave.acad_done = True
                    #
                    #         elif leave_request.leave.administrative_replacement == leave_request.requested_from:
                    #             leave_request.leave.admin_done = True
                    #
                    #             leave_request.leave.save()
                    #             condition = leave_request.leave.admin_done and leave_request.leave.acad_done
                    #
                    #             if condition:
                    #                 CurrentLeaveRequest.objects.get_or_create(
                    #                 leave = leave_request.leave,
                    #                 requested_from = sanc_auth,
                    #                 applicant = leave_request.applicant,
                    #                 position = sanc_auth,
                    #                 )
                    #
                    #
                    #             else:
                    #                 raise Http404
                    #
                    #             elif do == 'forward':
                    #
                    #                 if sanc_auth == sanc_officer and designation == sanc_auth:
                    #                     raise Http404
                    #
                    #                     condition = type_of_leave in ['casual', 'restricted'] \
                    #                     and designation == sanc_auth
                    #
                    #                     if condition:
                    #                         leave_request = self.create_leave_request(leave_request, False, accept=True, remark=remark)
                    #                         CurrentLeaveRequest.objects.create(
                    #                         leave = leave_request.leave,
                    #                         requested_from = sanc_officer,
                    #                         applicant = leave_request.applicant,
                    #                         position = sanc_officer,
                    #                         )
                    #
                    #                     else:
                    #                         raise Http404

"""
