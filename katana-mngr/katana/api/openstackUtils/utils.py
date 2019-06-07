import openstack
import functools
from multiprocessing import Process
# openstack.enable_logging(debug=True)


# wrapper for function, terminate after 5 seconds
def timeout(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        action = Process(target=func, args=args, kwargs=kwargs)
        action.start()
        action.join(timeout=5)
        if action.is_alive():
            # terminate function
            action.terminate()
            # clean up
            action.join()
            raise (TimeoutError)
        # if process is not 0, is not succesfull
        if action.exitcode != 0:
            # raise Attirbute Error, which is the most probable
            raise (AttributeError)
    return (wrapper)


# wraps the funcion
@timeout
def openstack_authorize(auth_url, project_name, username, password,
                        user_domain_name='Default',
                        project_domain_name='default'):

    conn = openstack.connect(
        auth_url=auth_url,
        project_name=project_name,
        username=username,
        password=password,
        user_domain_name=user_domain_name,
        project_domain_name=project_domain_name,
    )
    try:
        token = conn.authorize()
        print("authorized")
    except AttributeError as e:
        print("AttributeError baby")
        raise(e)
    except Exception as e:
        # raise for logging purposes
        raise(e)
    else:
        print("Token: ", token, flush=True)


def create_project(conn, name, description="Katana Slice Project"):
    # function expects name, password, a live connection to Openstack
    project = conn.identity.create_project(
        name=name, description=description)
    # returns Project object
    return project


def create_user(conn, name, password="password",
                description="Katana Slice User"):
    user = conn.identity.create_user(
        name=name, password=password, description=description)
    return user


def combine_proj_user(conn, project, user):
    userrole = conn.identity.find_role("user")
    heatrole = conn.identity.find_role("heat_stack_owner")
    conn.identity.assign_project_role_to_user(project, user, userrole)
    conn.identity.assign_project_role_to_user(project, user, heatrole)
    # Add admin user to the project, in order to create the MAC Addresses
    adminrole = conn.identity.find_role("admin")
    admin_user = conn.identity.find_user("admin", ignore_missing=False)
    conn.identity.assign_project_role_to_user(project, admin_user, adminrole)
    conn.identity.assign_project_role_to_user(project, admin_user, heatrole)


def create_sec_group(conn, name, project):
    """
    Creates the security group to be assigned to the new tenant
    """
    sec_group = conn.create_security_group(
        name=name, description="Katana Security Group", project_id=project.id)
    conn.create_security_group_rule(sec_group)
    return sec_group


def delete_user(conn, name):
    user = conn.identity.find_user(name, ignore_missing=False)
    conn.identity.delete_user(user, ignore_missing=False)


def delete_project(conn, name):
    project = conn.identity.find_project(name, ignore_missing=False)
    conn.identity.delete_project(project, ignore_missing=False)


def delete_proj_user(conn, name):
    try:
        delete_user(conn, name)
    except openstack.exceptions.ResourceNotFound as e:
        print("Failed. User trying to delete, doesn't exist")
    try:
        delete_project(conn, name)
    except openstack.exceptions.ResourceNotFound as e:
        print("Failed. Project trying to delete, doesn't exist")


def create_slice_prerequisites(tenant_project_name, tenant_project_description,
                               tenant_project_user, tenant_project_password,
                               selected_vim, slice_uuid):
    """
    Creates the tenant (project, user, security_group) on the specivied vim
    """

    auth_url = selected_vim['auth_url']
    admin_project_name = selected_vim['admin_project_name']
    username = selected_vim['username']
    password = selected_vim['password']

    vim_auth = dict(
        auth_url=auth_url,
        project_name=admin_project_name,
        username=username,
        password=password,
        user_domain_name='Default',
        project_domain_name='default')

    conn = openstack.connection.Connection(auth=vim_auth)

    # creates the project in Openstack
    project = create_project(conn, tenant_project_name,
                             tenant_project_description)

    # creates the user
    user = create_user(conn, tenant_project_user, "password")

    # assigns some needed roles
    combine_proj_user(conn, project, user)

    # creates the security group and rules
    sec_group = create_sec_group(conn, tenant_project_name, project)

    return {"sliceProjectId": project.id, "sliceUserId": user.id}
