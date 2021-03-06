from dal import autocomplete
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from chat import models as chat
from documents.models import Document
from groups import permissions
from supernova.views import build_base_context
from groups import models as m
from groups import forms as f
from chat import forms as chat_f


def index_view(request):
    context = build_base_context(request)
    context['title'] = "Grupos"
    context['pcode'] = "g"
    context['groups'] = m.Group.objects.prefetch_related('members').all()
    context['sub_nav'] = [{'name': 'Grupos', 'url': reverse('groups:index')}]
    return render(request, 'groups/groups.html', context)


def institutional_view(request):
    context = build_base_context(request)
    context['title'] = "Grupos"
    context['pcode'] = "g_inst"
    context['groups'] = m.Group.objects.prefetch_related('members').filter(
        Q(type=m.Group.ACADEMIC_ASSOCIATION) | Q(type=m.Group.INSTITUTIONAL)).all()
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        {'name': 'Institucionais', 'url': reverse('groups:institutional')}]
    return render(request, 'groups/groups.html', context)


def nuclei_view(request):
    context = build_base_context(request)
    context['title'] = "Grupos"
    context['pcode'] = "g_nucl"
    context['groups'] = m.Group.objects.prefetch_related('members').filter(type=m.Group.NUCLEI).all()
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        {'name': 'Núcleos', 'url': reverse('groups:nuclei')}]
    return render(request, 'groups/groups.html', context)


def pedagogic_view(request):
    context = build_base_context(request)
    context['title'] = "Grupos"
    context['pcode'] = "g_ped"
    context['groups'] = m.Group.objects.prefetch_related('members').filter(type=m.Group.PEDAGOGIC).all()
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        {'name': 'Pedagogicos', 'url': reverse('groups:pedagogic')}]
    return render(request, 'groups/groups.html', context)


def communities_view(request):
    context = build_base_context(request)
    context['title'] = "Grupos"
    context['pcode'] = "g_com"
    context['groups'] = m.Group.objects.prefetch_related('members').filter(type=m.Group.COMMUNITY).all()
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        {'name': 'Comunidades', 'url': reverse('groups:communities')}]
    return render(request, 'groups/groups.html', context)


def group_view(request, group_abbr):
    group = get_object_or_404(m.Group, abbreviation=group_abbr)
    permission_flags = 0 if request.user.is_anonymous else permissions.get_user_group_permissions(request.user, group)

    context = build_base_context(request)
    context['membership_perms'] = {
        'is_admin': permission_flags & permissions.IS_ADMIN,
        'can_announce': permission_flags & permissions.CAN_ANNOUNCE,
        'can_modify_roles': permission_flags & permissions.CAN_MODIFY_ROLES,
        'can_change_schedule': permission_flags & permissions.CAN_CHANGE_SCHEDULE}
    context['title'] = group.name
    context['group'] = group
    context['pcode'], nav_type = resolve_group_type(group)
    context['activities'] = m.Activity.objects.filter(group=group).order_by('datetime').reverse()
    context['is_member'] = is_member = not request.user.is_anonymous and group in request.user.groups_custom.all()

    if is_member:
        context['actions'] = [
            {'name': 'Sair do grupo', 'url': '#TODO'}]  # TODO
    else:
        if group.outsiders_openness == m.Group.REQUEST:
            context['actions'] = [
                {'name': 'Solicitar admissão', 'url': reverse('groups:membership_req', args=[group_abbr])}]
        elif group.outsiders_openness == m.Group.OPEN:
            context['actions'] = [
                {'name': 'Entrar no grupo', 'url': reverse('groups:membership_req', args=[group_abbr])}]

    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])}]
    return render(request, 'groups/group.html', context)


def announcements_view(request, group_abbr):
    group = get_object_or_404(m.Group, abbreviation=group_abbr)
    context = build_base_context(request)
    context['title'] = f'Anúncios de {group.name}'
    context['group'] = group
    context['pcode'], nav_type = resolve_group_type(group)
    context['announcements'] = m.Announcement.objects.filter(group=group).order_by('datetime').reverse()
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Anúncios', 'url': reverse('groups:announcements', args=[group_abbr])}]
    return render(request, 'groups/announcements.html', context)


def announcement_view(request, group_abbr, announcement_id):
    announcement = get_object_or_404(m.Announcement, id=announcement_id, group__abbreviation=group_abbr)
    group = announcement.group
    context = build_base_context(request)
    context['title'] = announcement.title
    context['group'] = group
    context['announcement'] = announcement
    pcode, nav_type = resolve_group_type(group)
    context['pcode'] = pcode + '_ann'
    context['announcements'] = m.Announcement.objects.filter(group=group).order_by('datetime').reverse()
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Anúncios', 'url': reverse('groups:announcements', args=[group_abbr])},
        {'name': announcement.title, 'url': reverse('groups:announcement', args=[group_abbr, announcement.id])}]
    return render(request, 'groups/announcement.html', context)


@login_required
def announce_view(request, group_abbr):
    group = get_object_or_404(m.Group, abbreviation=group_abbr)
    context = build_base_context(request)
    pcode, nav_type = resolve_group_type(group)
    context['pcode'] = pcode + '_announce'
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Anunciar', 'url': reverse('groups:announce', args=[group_abbr])}]

    permission_flags = permissions.get_user_group_permissions(request.user, group)
    if not (permission_flags & permissions.CAN_ANNOUNCE):
        context['title'] = context['msg_title'] = 'Insuficiência de permissões'
        context['msg_content'] = 'O seu utilizador não tem permissões suficientes para anúnciar pelo grupo.'
        return render(request, 'supernova/message.html', context)

    context['title'] = f'Anúnciar por {group.name}'
    context['group'] = group

    if request.method == 'POST':
        form = f.AnnounceForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.group = group
            announcement.author = request.user
            announcement.save()
            group.notify_subscribers(announcement)
            return redirect('groups:announcement', group_abbr=group_abbr, announcement_id=announcement.id)
    else:
        form = f.AnnounceForm()

    context['form'] = form
    return render(request, 'groups/announce.html', context)


def documents_view(request, group_abbr):
    group = get_object_or_404(m.Group, abbreviation=group_abbr)
    context = build_base_context(request)
    context['title'] = f'Documentos de {group.name}'
    context['group'] = group
    pcode, nav_type = resolve_group_type(group)
    context['pcode'] = pcode + '_doc'
    context['documents'] = Document.objects.filter(author_group=group).all()
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Documentos', 'url': reverse('groups:documents', args=[group_abbr])}]
    return render(request, 'groups/documents.html', context)


def members_view(request, group_abbr):
    group = get_object_or_404(
        m.Group.objects.prefetch_related('memberships__member', 'memberships__role'),
        abbreviation=group_abbr)
    context = build_base_context(request)
    context['title'] = f'Membros de {group.name}'
    context['group'] = group
    pcode, nav_type = resolve_group_type(group)
    context['pcode'] = pcode + '_memb'
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Membros', 'url': reverse('groups:members', args=[group_abbr])}]
    return render(request, 'groups/members.html', context)


@login_required
def group_membership_request_view(request, group_abbr):
    group = get_object_or_404(m.Group, abbreviation=group_abbr)

    if m.Membership.objects.filter(member=request.user, group=group).exists():
        return redirect('groups:group', group_abbr=group_abbr)

    # Find existing for past requests that have not been granted (pending + denied)
    existing_request = m.MembershipRequest.objects \
        .filter(user=request.user, group=group) \
        .exclude(granted=True) \
        .first()

    context = build_base_context(request)
    if previously_requested := (existing_request is not None):
        if existing_request.granted is not None:  # Has been denied once, can no longer request
            raise PermissionDenied("Membership has been refused.")

        # \/ Deletion secret. Not the best secret, but this is unlikely to get attacked
        secret = str(existing_request.id)
        if 'remove' in request.GET:
            # Deleting existing request (pending request without neither approval nor disapproval)
            if request.GET['remove'] == secret:
                existing_request.delete()
                return redirect('groups:group', group_abbr=group_abbr)
            else:
                raise PermissionDenied("No authorization to post in this conversation.")
        # Warning the user that a pending request exists, show no form
        form = None
        context['secret'] = secret
        context['pending'] = existing_request.granted is None
    else:  # First request

        # Requests towards open groups are translated to a direct membership
        if group.outsiders_openness == m.Group.OPEN:
            if group.default_role_id is not None:
                m.Membership.objects.create(member=request.user, group=group, role_id=group.default_role_id)
                return redirect('groups:group', group_abbr=group_abbr)

        # Can't request membership to closed groups
        if group.outsiders_openness != m.Group.REQUEST:
            raise PermissionDenied("Membership requested in a closed or secret group.")

        if request.method == "POST":
            form = f.MembershipRequestForm(request.POST)
            if form.is_valid():
                message = form.cleaned_data['message']
                if isinstance(message, str):
                    message = message.strip()
                m.MembershipRequest.objects.create(user=request.user, group=group, message=message)
                return redirect('groups:membership_req', group_abbr=group_abbr)
        else:
            form = f.MembershipRequestForm()

    context['title'] = f'Solicitar admissão em {group.name}'
    context['group'] = group
    context['form'] = form
    context['previously_requested'] = previously_requested
    pcode, nav_type = resolve_group_type(group)
    context['pcode'] = pcode + '_memb_req'
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Solicitar admissão', 'url': reverse('groups:membership_req', args=[group_abbr])}]
    return render(request, 'groups/membership_request.html', context)


@login_required
def group_candidates_view(request, group_abbr):
    group = get_object_or_404(m.Group.objects.select_related('default_role'), abbreviation=group_abbr)

    # Check for permissions
    permission_flags = 0 if request.user.is_anonymous else permissions.get_user_group_permissions(request.user, group)
    roles_acc = permission_flags & permissions.CAN_ASSIGN_ROLES
    if not roles_acc:
        raise PermissionDenied("No permission to manage roles.")

    accepted = request.GET.get('accept')
    denied = request.GET.get('deny')
    try:
        if accepted:
            m.MembershipRequest.objects.get(id=int(accepted)).accept()
        elif denied:
            m.MembershipRequest.objects.get(id=int(accepted)).deny()
    except ValueError:
        pass

    pcode, nav_type = resolve_group_type(group)
    context = build_base_context(request)
    context['title'] = f'Candidaturas a {group.name}'
    context['default_role'] = group.default_role
    context['candidates'] = m.MembershipRequest.objects.filter(group=group, granted=None).select_related('user').all()
    context['group'] = group
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Candidatos', 'url': reverse('groups:candidates', args=[group_abbr])}]
    return render(request, 'groups/membership_requests.html', context)


@login_required
def conversations_view(request, group_abbr):
    group = get_object_or_404(m.Group, abbreviation=group_abbr)
    permission_flags = 0 if request.user.is_anonymous else permissions.get_user_group_permissions(request.user, group)
    read_acc = permission_flags & permissions.CAN_READ_CONVERSATIONS
    context = build_base_context(request)
    context['title'] = f'Contactos com {group.name}'
    context['group'] = group
    pcode, nav_type = resolve_group_type(group)
    context['pcode'] = pcode + '_cnt'
    if read_acc:
        context['conversations'] = chat.GroupExternalConversation.objects \
            .filter(group=group) \
            .order_by('-creation') \
            .select_related('last_activity_user')
    else:
        context['conversations'] = chat.GroupExternalConversation.objects \
            .filter(group=group, creator=request.user) \
            .exclude(creator=request.user) \
            .order_by('-creation') \
            .select_related('last_activity_user')
    context['actions'] = [
        {'name': 'Criar nova', 'url': reverse('groups:conversation_create', args=[group_abbr])}]
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Conversas', 'url': reverse('groups:conversations', args=[group_abbr])}]
    return render(request, 'groups/conversations.html', context)


@login_required
def conversation_create_view(request, group_abbr):
    group = get_object_or_404(m.Group, abbreviation=group_abbr)
    context = build_base_context(request)

    if request.method == "POST":
        form = f.GroupExternalConversationCreation(request.POST)
        if form.is_valid():
            message = form.cleaned_data['message']
            if isinstance(message, str):
                message = message.strip()
            conversation = form.save(commit=False)
            conversation.group = group
            conversation.creator = request.user
            conversation.last_activity_user = request.user
            conversation.save()
            conversation.users.add(request.user)
            chat.Message.objects.create(author=request.user, content=message, conversation=conversation)
            if not group.official:
                # TODO Redirect message elsewhere
                pass
            return redirect('groups:conversation', group_abbr=group_abbr, conversation_id=conversation.id)
    else:
        form = f.GroupExternalConversationCreation()

    context['title'] = f'Contactar {group.name}'
    context['group'] = group
    pcode, nav_type = resolve_group_type(group)
    context['pcode'] = pcode + '_cnt'
    context['form'] = form
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Conversas', 'url': reverse('groups:conversations', args=[group_abbr])},
        {'name': 'Nova conversa', 'url': reverse('groups:conversation_create', args=[group_abbr])}]
    return render(request, 'groups/conversation_create.html', context)


@login_required
def conversation_view(request, group_abbr, conversation_id):
    group = get_object_or_404(m.Group, abbreviation=group_abbr)
    conversation = get_object_or_404(chat.GroupExternalConversation, id=conversation_id, group=group)

    permission_flags = 0 if request.user.is_anonymous else permissions.get_user_group_permissions(request.user, group)
    is_author = conversation.creator == request.user  # TODO: Change creator to is member of (use the conversation m2m)
    read_acc = permission_flags & permissions.CAN_READ_CONVERSATIONS
    write_acc = permission_flags & permissions.CAN_WRITE_CONVERSATIONS
    if not is_author and not read_acc:
        # FIXME this allows finding that this conversation exists (as it does not 404)
        # maybe change conversation identifiers to URL slugs to make it inviable to brute force URLs.
        raise PermissionDenied("No authorization to view this conversation.")

    if request.method == 'POST':
        if not (is_author or write_acc):
            raise PermissionDenied("No authorization to post in this conversation.")

        message_form = chat_f.MessageForm(request.POST)
        if message_form.is_valid():
            message = message_form.save(commit=False)
            message.author = request.user
            message.conversation = conversation
            message.save()
            message_form = chat_f.MessageForm()
    else:
        message_form = chat_f.MessageForm()

    messages = chat.Message.objects \
        .filter(conversation=conversation) \
        .order_by('creation') \
        .select_related('author') \
        .all()
    context = build_base_context(request)
    context['title'] = f'Contactar {group.name}'
    context['group'] = group
    context['conversation'] = conversation
    context['messages'] = messages
    if write_acc:
        context['message_form'] = message_form
    pcode, nav_type = resolve_group_type(group)
    context['pcode'] = pcode + '_cnt'
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Conversas', 'url': reverse('groups:conversations', args=[group_abbr])},
        {'name': conversation.title, 'url': reverse('groups:conversation', args=[group_abbr, conversation_id])}]
    return render(request, 'groups/conversation.html', context)


@login_required
def settings_view(request, group_abbr):
    group = get_object_or_404(m.Group, abbreviation=group_abbr)
    context = build_base_context(request)
    pcode, nav_type = resolve_group_type(group)
    context['pcode'] = pcode + '_settings'
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Definições', 'url': reverse('groups:settings', args=[group_abbr])}]

    permission_flags = permissions.get_user_group_permissions(request.user, group)
    if not (permission_flags & permissions.IS_ADMIN):
        context['title'] = context['msg_title'] = 'Insuficiência de permissões'
        context['msg_content'] = 'O seu utilizador não tem permissões suficientes para mudar as definições do grupo.'
        return render(request, 'supernova/message.html', context)

    context['title'] = f'Definições de {group.name}'
    context['group'] = group

    if request.method == 'POST':
        group_form = f.GroupSettingsForm(request.POST, request.FILES, instance=group)
        if group_form.is_valid():
            group_form.save()
            return redirect('groups:group', group_abbr=group_abbr)
    else:
        group_form = f.GroupSettingsForm(instance=group)

    context['group_form'] = group_form
    return render(request, 'groups/settings.html', context)


@login_required
def roles_view(request, group_abbr):
    group = get_object_or_404(m.Group, abbreviation=group_abbr)
    context = build_base_context(request)
    pcode, nav_type = resolve_group_type(group)
    context['pcode'] = pcode + '_roles'
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Cargos', 'url': reverse('groups:roles', args=[group_abbr])}]

    permission_flags = permissions.get_user_group_permissions(request.user, group)
    if not (permission_flags & permissions.CAN_MODIFY_ROLES or permission_flags & permissions.CAN_ASSIGN_ROLES):
        context['title'] = context['msg_title'] = 'Insuficiência de permissões'
        context['msg_content'] = 'O seu utilizador não tem permissões suficientes para mudar os cargos do grupo.'
        return render(request, 'supernova/message.html', context)

    context['title'] = f'Gerir cargos de {group.name}'
    context['group'] = group
    context['can_edit'] = permission_flags & permissions.CAN_MODIFY_ROLES
    if request.method == 'POST':
        membership_formset = f.GroupMembershipFormSet(
            request.user,
            request.POST,
            instance=group,
            queryset=group.memberships)
        if membership_formset.is_valid():
            membership_formset.save()
            # Reset formset data to remove deleted
            membership_formset = f.GroupMembershipFormSet(
                request.user,
                instance=group,
                queryset=group.memberships)
    else:
        membership_formset = f.GroupMembershipFormSet(
            request.user,
            instance=group,
            queryset=group.memberships)

    context['membership_formset'] = membership_formset
    return render(request, 'groups/roles.html', context)


@login_required
def role_view(request, group_abbr, role_id):
    group = get_object_or_404(m.Group, abbreviation=group_abbr)
    context = build_base_context(request)
    pcode, nav_type = resolve_group_type(group)
    context['pcode'] = pcode + '_role'
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Cargos', 'url': reverse('groups:roles', args=[group_abbr])}]

    permission_flags = permissions.get_user_group_permissions(request.user, group)
    if not permission_flags & permissions.CAN_MODIFY_ROLES:
        context['title'] = context['msg_title'] = 'Insuficiência de permissões'
        context['msg_content'] = 'O seu utilizador não tem permissões suficientes para mudar os cargos do grupo.'
        return render(request, 'supernova/message.html', context)

    context['group'] = group
    context['role_id'] = role_id

    if role_id == 0:
        context['title'] = f'Criar cargo'
        if request.method == 'POST':
            form = f.RoleForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('groups:roles', group_abbr=group_abbr)
        else:
            form = f.RoleForm()
            context['sub_nav'].append({'name': "Criar cargo", 'url': reverse('groups:role', args=[group_abbr, 0])})
    else:
        role = get_object_or_404(m.Role, id=role_id, group__abbreviation=group_abbr)
        if request.method == 'POST':
            form = f.RoleForm(request.POST, instance=role)
            if form.is_valid():
                form.save()
                return redirect('groups:roles', group_abbr=group_abbr)
        else:
            form = f.RoleForm(instance=role)

        context['role'] = role
        context['title'] = f'Edição do cargo {role.name}'
        context['sub_nav'].append({'name': role.name, 'url': reverse('groups:role', args=[group_abbr, role_id])})
    context['form'] = form
    return render(request, 'groups/role.html', context)


@login_required
def calendar_management_view(request, group_abbr):
    group = get_object_or_404(m.Group, abbreviation=group_abbr)

    if 'del' in request.GET:
        try:
            del_id = int(request.GET['del'])
            m.ScheduleEntry.objects.get(id=del_id, group=group).delete()
            return redirect('users:calendar_manage', abbreviation=group_abbr)
        except (ValueError, m.ScheduleOnce.DoesNotExist):
            return HttpResponse(status=400)

    context = build_base_context(request)
    pcode, nav_type = resolve_group_type(group)
    context['pcode'] = pcode + '_cal_man'

    permission_flags = permissions.get_user_group_permissions(request.user, group)
    if not permission_flags & permissions.CAN_CHANGE_SCHEDULE:
        context['title'] = context['msg_title'] = 'Insuficiência de permissões'
        context['msg_content'] = 'O seu utilizador não tem permissões suficientes para alterar a agenda do grupo.'
        return render(request, 'supernova/message.html', context)

    context['group'] = group
    once_schedule_entries = m.ScheduleOnce.objects.filter(group=group)
    periodic_schedule_entries = m.SchedulePeriodic.objects.filter(group=group)
    context['once_entries'] = once_schedule_entries
    context['periodic_entries'] = periodic_schedule_entries

    # Show empty forms by default
    once_form = f.ScheduleOnceForm()
    periodic_form = f.SchedulePeriodicForm()
    if 'type' in request.GET:
        rtype = request.GET['type']
        if rtype == "periodic" and request.method == 'POST':
            filled_form = f.SchedulePeriodicForm(request.POST)
            if filled_form.is_valid():
                entry = filled_form.save(commit=False)
                entry.group = group
                entry.save()
                m.ScheduleCreation.objects.create(group=group, author=request.user, entry=entry)
            else:
                periodic_form = filled_form  # Replace empty form with filled form with form filled with errors
        elif rtype == "once" and request.method == 'POST':
            filled_form = f.ScheduleOnceForm(request.POST)
            if filled_form.is_valid():
                entry = filled_form.save(commit=False)
                entry.group = group
                entry.save()
                m.ScheduleCreation.objects.create(group=group, author=request.user, entry=entry)
            else:
                once_form = filled_form  # Replace empty form with form filled with errors

    context['once_form'] = once_form
    context['periodic_form'] = periodic_form
    context['sub_nav'] = [
        {'name': 'Grupos', 'url': reverse('groups:index')},
        nav_type,
        {'name': group.abbreviation, 'url': reverse('groups:group', args=[group_abbr])},
        {'name': 'Agenda', 'url': reverse('groups:calendar_manage', args=[group_abbr])}]

    return render(request, 'groups/calendar_manage.html', context)


class GroupRolesAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        group = self.forwarded.get('group', None)
        if group is None or group == '':
            return []
        qs = m.Role.objects.filter(group=group)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


def resolve_group_type(group):
    code = m.Group.GROUP_CODES[group.type]
    pcode = f'g_{code}'
    if code == 'inst':
        nav = {'name': 'Institucionais', 'url': reverse('groups:institutional')}
    elif code == 'nucl':
        nav = {'name': 'Núcleos', 'url': reverse('groups:nuclei')}
    elif code == 'ped':
        nav = {'name': 'Pedagogicos', 'url': reverse('groups:pedagogic')}
    elif code == 'com':
        nav = {'name': 'Comunidades', 'url': reverse('groups:communities')}
    else:
        nav = {'name': '?', 'url': '#'}
    return pcode, nav
