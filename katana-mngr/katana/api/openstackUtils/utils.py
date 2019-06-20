import openstack
import functools
from multiprocessing import Process
# openstack.enable_logging(debug=True)
import logging

# Logging Parameters
logger = logging.getLogger(__name__)
file_handler = logging.handlers.RotatingFileHandler(
    'katana.log', maxBytes=10000, backupCount=5)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
stream_formatter = logging.Formatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def timeout(func):
    """
    Wrapper for function, terminate after 5 seconds
    """
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


class Openstack():
    """
    Class implementing the communication API with OpenStack
    """
    # Note: Cannot use conn as a self variable, as it is not possible to
    # serialize it and store it in a db

    def __init__(self, uuid, auth_url, project_name, username, password,
                 user_domain_name='Default',
                 project_domain_name='default'):
        """
        Initialize an object of the class
        """
        self.uuid = uuid
        self.auth_url = auth_url
        self.project_name = project_name
        self.username = username
        self.password = password
        self.user_domain_name = user_domain_name
        self.project_domain_name = project_domain_name
        conn = openstack.connect(
            auth_url=self.auth_url,
            project_name=self.project_name,
            username=self.username,
            password=self.password,
            user_domain_name=self.user_domain_name,
            project_domain_name=self.project_domain_name,
            )
        try:
            conn.authorize()
        except AttributeError as e:
            logger.exception("AttributeError baby")
            self.auth_error = True
        except Exception as e:
            # raise for logging purposes
            logger.exception("Something went wrong", e)
            self.auth_error = True
        else:
            self.auth_error = False

    @timeout
    def openstack_authorize(self, conn):
        """
        Returns a token for the OpenStack instance
        """
        try:
            _ = conn.authorize()
        except AttributeError as e:
            logger.exception("AttributeError baby")
            return True
        except Exception as e:
            # raise for logging purposes
            logger.exception("Something went wrong", e)
            return True
        else:
            return False

    def create_project(self, conn, name, description="Katana Slice Project"):
        """
        Creates a new openstack project
        """
        project = conn.identity.create_project(name=name,
                                               description=description)
        # returns Project object
        return project

    def create_user(self, conn, name, password="password",
                    description="Katana Slice User"):
        """
        Creates a new openstack project
        """
        user = conn.identity.create_user(name=name, password=password,
                                         description=description)
        return user

    def combine_proj_user(self, conn, project, user):
        """
        Compbines newly created project and user
        """
        userrole = conn.identity.find_role("user")
        heatrole = conn.identity.find_role("heat_stack_owner")
        conn.identity.assign_project_role_to_user(project, user, userrole)
        conn.identity.assign_project_role_to_user(project, user, heatrole)
        # Add admin user to the project, in order to create the MAC Addresses
        adminrole = conn.identity.find_role("admin")
        admin_user = conn.identity.find_user("admin", ignore_missing=False)
        conn.identity.assign_project_role_to_user(project, admin_user,
                                                  adminrole)
        conn.identity.assign_project_role_to_user(project, admin_user,
                                                  heatrole)

    def create_sec_group(self, conn, name, project):
        """
        Creates the security group to be assigned to the new tenant
        """
        sec_group = conn.create_security_group(
            name=name, description="Katana Security Group",
            project_id=project.id)
        conn.create_security_group_rule(sec_group)
        return sec_group

    def delete_user(self, conn, name):
        """
        Deletes the user
        """
        user = conn.identity.find_user(name, ignore_missing=False)
        conn.identity.delete_user(user, ignore_missing=False)

    def delete_project(self, conn, name):
        """
        Deletes the user
        """
        project = conn.identity.find_project(name, ignore_missing=False)
        conn.identity.delete_project(project, ignore_missing=False)

    def delete_sec_group(self, conn, name):
        """
        Deletes the security group
        """
        conn.delete_security_group(name)

    def delete_proj_user(self, tenant):
        """
        Deletes user and project
        """
        conn = openstack.connect(
            auth_url=self.auth_url,
            project_name=self.project_name,
            username=self.username,
            password=self.password,
            user_domain_name=self.user_domain_name,
            project_domain_name=self.project_domain_name,
            )
        self.openstack_authorize(conn)
        user_name = tenant["sliceUserName"]
        project_name = tenant["sliceProjectName"]
        sec_group_name = tenant["secGroupName"]
        try:
            self.delete_user(conn, user_name)
        except openstack.exceptions.ResourceNotFound as e:
            logger.exception("Failed. User trying to delete, doesn't exist")
        try:
            self.delete_project(conn, project_name)
        except openstack.exceptions.ResourceNotFound as e:
            logger.exception("Failed. Project trying to delete, doesn't exist")
        try:
            self.delete_sec_group(conn, sec_group_name)
        except openstack.exceptions.ResourceNotFound as e:
            logger.exception("Failed. Security group trying to delete, doesn't\
                exist", e)

    def create_slice_prerequisites(self, tenant_project_name,
                                   tenant_project_description,
                                   tenant_project_user,
                                   tenant_project_password,
                                   slice_uuid):
        """
        Creates the tenant (project, user, security_group) on the specivied vim
        """
        conn = openstack.connect(
            auth_url=self.auth_url,
            project_name=self.project_name,
            username=self.username,
            password=self.password,
            user_domain_name=self.user_domain_name,
            project_domain_name=self.project_domain_name,
            )
        self.openstack_authorize(conn)
        # creates the project in Openstack
        project = self.create_project(conn, tenant_project_name,
                                      tenant_project_description)

        # creates the user
        user = self.create_user(conn, tenant_project_user, "password")

        # assigns some needed roles
        self.combine_proj_user(conn, project, user)

        # creates the security group and rules
        sec_group = self.create_sec_group(conn, tenant_project_name, project)

        return {"sliceProjectName": project.name, "sliceUserName": user.name,
                "secGroupName": sec_group.name}
