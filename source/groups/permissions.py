from groups import models as m

IS_ADMIN = 1
CAN_MODIFY_ROLES = 1 << 1
CAN_ASSIGN_ROLES = 1 << 2
CAN_ANNOUNCE = 1 << 3
CAN_READ_CONVERSATIONS = 1 << 4
CAN_WRITE_CONVERSATIONS = 1 << 5
CAN_READ_INTERNAL_CONVERSATIONS = 1 << 6
CAN_WRITE_INTERNAL_CONVERSATIONS = 1 << 7
CAN_READ_INTERNAL_DOCUMENTS = 1 << 8
CAN_WRITE_INTERNAL_DOCUMENTS = 1 << 9
CAN_WRITE_PUBLIC_DOCUMENTS = 1 << 10
CAN_CHANGE_SCHEDULE = 1 << 11


def roles_combined(roles):
    """
    Combines the existing set of permissions from a set of roles.
    :param roles: An iterable collection of py:class:`group.model.Role` objects.
    :return: Integer with the binary permission flags
    """
    permissions = 0
    for role in roles:
        if role.is_admin:
            permissions = (1 << 12) - 1
        if role.can_modify_roles:
            permissions = permissions | CAN_MODIFY_ROLES
        if role.can_assign_roles:
            permissions = permissions | CAN_ASSIGN_ROLES
        if role.can_announce:
            permissions = permissions | CAN_ANNOUNCE
        if role.can_read_conversations:
            permissions = permissions | CAN_READ_CONVERSATIONS
        if role.can_write_conversations:
            permissions = permissions | CAN_WRITE_CONVERSATIONS
        if role.can_read_internal_conversations:
            permissions = permissions | CAN_READ_INTERNAL_CONVERSATIONS
        if role.can_write_internal_conversations:
            permissions = permissions | CAN_WRITE_INTERNAL_CONVERSATIONS
        if role.can_read_internal_documents:
            permissions = permissions | CAN_READ_INTERNAL_DOCUMENTS
        if role.can_write_internal_documents:
            permissions = permissions | CAN_WRITE_INTERNAL_DOCUMENTS
        if role.can_write_public_documents:
            permissions = permissions | CAN_WRITE_PUBLIC_DOCUMENTS
        if role.can_change_schedule:
            permissions = permissions | CAN_CHANGE_SCHEDULE
    return permissions


def get_user_group_permissions(user, group):
    """
    Compiles a binary mask with the permissions a user has on a given group.
    :param user: User to whom the permissions refer
    :param group: Group to which the permissions refer
    :return: Permission mask
    """
    roles = m.Role.objects.filter(
        memberships__member=user,
        memberships__group=group)
    return roles_combined(roles)


def can_handle_permissions(handler_permissions, handled_permissions):
    """
    Checks if a given set of permissions can modify users with another set of permissions.
    :param handler_permissions: Modifier user permissions
    :param handled_permissions: Modified user permissions
    :return: Bool value confirming allowance
    """
    if not handler_permissions & CAN_ASSIGN_ROLES:
        return False

    # permissions must have at least all of the role permissions
    return handled_permissions == handler_permissions & handled_permissions
