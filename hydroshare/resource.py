### resource API
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from mezzanine.generic.models import Keyword, AssignedKeyword
from dublincore.models import QualifiedDublinCoreElement
from hs_core.hydroshare.utils import get_resource_types
from hs_core.models import ResourceFile
from . import utils


def get_resource(pk):
    """
    Retrieve a resource identified by the pid from HydroShare. The response must contain the bytes of the indicated
    resource, and the checksum of the bytes retrieved should match the checksum recorded in the system metadata for
    that resource. The bytes of the resource will be encoded as a zipped BagIt archive; this archive will contain
    resource contents as well as science metadata. If the resource does not exist in HydroShare, then
    Exceptions.NotFound must be raised. Resources can be any unit of content within HydroShare that has been assigned a
    pid.

    Parameters:    pk - Unique HydroShare identifier for the resource to be retrieved.

    Returns:    Bytes of the specified resource.

    Return Type:    OctetStream

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Notes:
    All resources and resource versions will have a unique internal HydroShare identifier (pid). A DOI will be
    assigned to all formally published versions of a resource. For this method, passing in a pid (which is a HydroShare
    internal identifer) would return a specific resource version corresponding to the pid. A DOI would have to be
    resolved using HydroShare.resolveDOI() to get the pid for the resource, which could then be used with this method.
    The obsoletion chain will be contained within the system metadata for resources and so it can be traversed by
    calling HydroShare.getSystemMetadata().
    """

    # 1. Look up the resource by ID
    # 2. Check to see if a bagit file exists on IRODS for that resource
    # 3.T.1. Return the bagit file
    # 3.F.1. look up the resource serialization (tastypie) class in the resource type map
    # 3.F.2. Serialize the resource to disk using TastyPie.
    # 3.F.3. Create a bagit file from the serialized resource.
    # 3.F.4. Return the bagit file
    return utils.get_resource_by_shortkey(pk).bags.first()


def get_science_metadata(pk):
    """
    Describes the resource identified by the pid by returning the associated science metadata object. If the resource
    does not exist, Exceptions.NotFound must be raised.

    REST URL:  GET /scimeta/{pid}

    Parameters:    pk  - Unique HydroShare identifier for the resource whose science metadata is to be retrieved.

    Returns:    Science metadata document describing the resource.

    Return Type:    ScienceMetadata

    Raises:    Exceptions.NotAuthorized -  The user is not authorized
    Exceptions.NotFound  - The resource identified by pid does not exist
    Exception.ServiceFailure  - The service is unable to process the request
    """
    return get_system_metadata(pk)


def get_system_metadata(pk):
    """
    Describes the resource identified by the pid by returning the associated system metadata object. If the resource
    does not exist, Exceptions.NotFound must be raised.

    REST URL:  GET /sysmeta/{pid}

    Parameters:    pk - Unique HydroShare identifier for the resource whose system metadata is to be retrieved.

    Returns:    System metadata document describing the resource.

    Return Type:    SystemMetadata

    Raises:
        Exceptions.NotAuthorized - The user is not authorized
        Exceptions.NotFound - The resource identified by pid does not exist
        Exception.ServiceFailure - The service is unable to process the request
    """
    return utils.get_resource_by_shortkey(pk)


def get_resource_map(pk):
    """
    Describes the resource identified by the pid by returning the associated resource map document. If the resource does
    not exist, Exceptions.NotFound must be raised.

    REST URL:  GET /resourcemap/{pid}

    Parameters:    pid - Unique HydroShare identifier for the resource whose resource map is to be retrieved.

    Returns:    Resource map document describing the resource.

    Return Type:    ResourceMap

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    return utils.get_resource_by_shortkey(pk)


def get_capabilities(pk):
    """
    Describes API services exposed for a resource.  If there are extra capabilites for a particular resource type over
    and above the standard Hydroshare API, then this API call will list these

    REST URL: GET /capabilites/{pid}

    Parameters: Unique HydroShare identifier for the resource whose capabilites are to be retrieved.

    Return Type: Capabilites

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    res = utils.get_resource_by_shortkey(pk)
    return getattr(res, 'extra_capabilities', lambda: None)()


def get_resource_file(pk, filename):
    """
    Called by clients to get an individual file within a HydroShare resource.

    REST URL:  GET /resource/{pid}/files/{filename}

    Parameters:
    pid - Unique HydroShare identifier for the resource from which the file will be extracted.
    filename - The data bytes of the file that will be extracted from the resource identified by pid

    Returns: The bytes of the file extracted from the resource

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified does not exist or the file identified by filename does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    resource = utils.get_resource_by_shortkey(pk)
    for f in ResourceFile.objects.filter(content_object=resource):
        if f.resource_file.name == filename:
            return f.resource_file
    else:
        raise ObjectDoesNotExist(filename)


def update_resource_file(pk, filename, f):
    """
    Called by clients to update an individual file within a HydroShare resource.

    REST URL:  PUT /resource/{pid}/files/{filename}

    Parameters:
    pid - Unique HydroShare identifier for the resource from which the file will be extracted.
    filename - The data bytes of the file that will be extracted from the resource identified by pid
    file - the data bytes of the file to update

    Returns: The bytes of the file extracted from the resource

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified does not exist or the file identified by filename does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    resource = utils.get_resource_by_shortkey(pk)
    for rf in ResourceFile.objects.filter(content_object=resource):
        if rf.resource_file.name == filename:
            rf.resource_file = File(f) if not isinstance(f, UploadedFile) else f
            rf.save()
        return rf
    else:
        raise ObjectDoesNotExist(filename)

def get_revisions(pk):
    """
    Returns a list of pids for resources that are revisions of the resource identified by the specified pid.

    REST URL:  GET /revisions/{pid}

    Parameters:    pid - Unique HydroShare identifier for the resource whose revisions are to be retrieved.

    Returns: List of pids for resources that are revisions of the specified resource.

    Return Type: List of pids

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The Resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request

    """
    return utils.get_resource_by_shortkey(pk).bags.all()


def get_related(pk):
    """
    Returns a list of pids for resources that are related to the resource identified by the specified pid.

    REST URL:  GET /related/{pid}

    Parameters:
    pid - Unique HydroShare identifier for the resource whose related resources are to be retrieved.

    Returns:    List of pids for resources that are related to the specified resource.

    Return Type:    List of pids

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request


    """
    raise NotImplemented()


def get_checksum(pk):
    """
    Returns a checksum for the specified resource using the MD5 algorithm. The result is used to determine if two
    instances referenced by a pid are identical.

    REST URL:  GET /checksum/{pid}

    Parameters:
    pid - Unique HydroShare identifier for the resource for which the checksum is to be returned.

    Returns:    Checksum of the resource identified by pid.

    Return Type:    Checksum

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource specified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    raise NotImplemented()


def create_resource(
        resource_type, owner, title,
        edit_users=None, view_users=None, edit_groups=None, view_groups=None,
        keywords=None, dublin_metadata=None,
        *files, **kwargs):
    """
    Called by a client to add a new resource to HydroShare. The caller must have authorization to write content to
    HydroShare. The pid for the resource is assigned by HydroShare upon inserting the resource.  The create method
    returns the newly-assigned pid.

    REST URL:  POST /resource

    Parameters:
    resource - The data bytes of the resource to be added to HydroShare

    Returns:    The pid assigned to the newly created resource

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized to write to HydroShare
    Exceptions.InvalidContent - The content of the resource is incomplete
    Exception.ServiceFailure - The service is unable to process the request

    Note:  The calling user will automatically be set as the owner of the created resource.
    """
    for tp in get_resource_types():
        if resource_type == tp.__name__:
            cls = tp
            break
    else:
        raise NotImplemented("Type {resource_type} does not exist".format(**locals()))

    # create the resource
    resource = cls.objects.create(
        user=owner,
        author=owner,
        title=title,
        **kwargs
    )
    for file in files:
        ResourceFile.objects.create(content_object=resource, resource_file=file)

    resource.view_users.add(owner)
    resource.edit_users.add(owner)
    resource.owners.add(owner)

    if edit_users:   
        for user in edit_users:
            user = utils.user_from_id(user)
            resource.edit_users.add(user)
            resource.view_users.add(user)
    if view_users:
        for user in view_users:
            user = utils.user_from_id(user)
            resource.view_users.add(user)
    
    if edit_groups:   
        for group in edit_groups:
            group = utils.group_from_id(group)
            resource.edit_groups.add(group)
            resource.view_groups.add(group)
    if view_groups:
        for group in view_groups:
            group = utils.group_from_id(group)
            resource.view_groups.add(group)

    if keywords:
        ks = [Keyword.objects.get_or_create(k) for k in keywords]
        ks = zip(*ks)[0]  # ignore whether something was created or not.  zip is its own inverse

        for k in ks:
            AssignedKeyword.objects.create(content_object=resource, keyword=k)

    if dublin_metadata:
        for d in dublin_metadata:
            QualifiedDublinCoreElement.objects.create(
                term=d['term'],
                qualifier=d.get('qualifier'),
                content=d['content'],
                content_object=resource
            )

    return resource
        

def update_resource(
        pk,
        edit_users=None, view_users=None, edit_groups=None, view_groups=None,
        keywords=None, dublin_metadata=None,
        *files, **kwargs):
    """
    Called by clients to update a resource in HydroShare.

    REST URL:  PUT /resource/{pid}

    Parameters:
    pid - Unique HydroShare identifier for the resource that is to be updated.

    resource - The data bytes of the resource that will update the existing resource identified by pid

    Returns:    The pid assigned to the updated resource

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.InvalidContent - The content of the resource is incomplete
    Exception.ServiceFailure - The service is unable to process the request

    Notes:
    For mutable resources (resources that have not been formally published), the update overwrites existing data and
    metadata using the resource that is passed to this method. If a user wants to create a copy or modified version of a
    mutable resource this should be done using HydroShare.createResource().

    For immutable resources (formally published resources), this method creates a new resource that is a new version of
    formally published resource. HydroShare will record the update by storing the SystemMetadata.obsoletes and
    SystemMetadata.obsoletedBy fields for the respective resources in their system metadata.HydroShare MUST check or set
    the values of SystemMetadata.obsoletes and SystemMetadata.obsoletedBy so that they accurately represent the
    relationship between the new and old objects. HydroShare MUST also set SystemMetadata.dateSysMetadataModified. The
    modified system metadata entries must then be available in HydroShare.listObjects() to ensure that any cataloging
    systems pick up the changes when filtering on SystmeMetadata.dateSysMetadataModified. A formally published resource
    can only be obsoleted by one newer version. Once a resource is obsoleted, no other resources can obsolete it.
    """
    resource = utils.get_resource_by_shortkey(pk)

    if files:
        ResourceFile.objects.filter(content_object=resource).delete()
        for file in files:
            ResourceFile.objects.create(
                content_object=resource,
                resource_file=File(file) if not isinstance(file, UploadedFile) else file
            )

    if 'owner' in kwargs:
        owner = kwargs['owner']
        resource.view_users.add(owner)
        resource.edit_users.add(owner)
        resource.owners.add(owner)

    if edit_users:
        resource.edit_users.clear()
        for user in edit_users:
            user = utils.user_from_id(user)
            resource.edit_users.add(user)
            resource.view_users.add(user)

    if view_users:
        resource.view_users.clear()
        for user in view_users:
            user = utils.user_from_id(user)
            resource.view_users.add(user)

    if edit_groups:
        resource.edit_groups.clear()
        for group in edit_groups:
            group = utils.group_from_id(group)
            resource.edit_groups.add(group)
            resource.view_groups.add(group)

    if view_groups:
        resource.edit_groups.clear()
        for group in view_groups:
            group = utils.group_from_id(group)
            resource.view_groups.add(group)

    if keywords:
        AssignedKeyword.objects.filter(content_object=resource).delete()
        ks = [Keyword.objects.get_or_create(k) for k in keywords]
        ks = zip(*ks)[0]  # ignore whether something was created or not.  zip is its own inverse

        for k in ks:
            AssignedKeyword.objects.create(content_object=resource, keyword=k)

    if dublin_metadata:
        QualifiedDublinCoreElement.objects.filter(content_object=resource).delete()
        for d in dublin_metadata:
            QualifiedDublinCoreElement.objects.create(
                term=d['term'],
                qualifier=d.get('qualifier'),
                content=d['content'],
                content_object=resource
            )

    return resource

def add_resource_files(pk, *files):
    """
    Called by clients to update a resource in HydroShare by adding a single file.

    REST URL:  PUT /resource/{pid}/files/{file}

    Parameters:
    pid - Unique HydroShare identifier for the resource that is to be updated.
    file - The data bytes of the file that will be added to the existing resource identified by pid

    Returns:    The pid assigned to the updated resource

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.InvalidContent - The content of the file is invalid
    Exception.ServiceFailure - The service is unable to process the request

    Notes:
    For mutable resources (resources not formally published), the update adds the file that is passed
    to this method to the resource. For immutable resources (formally published resources), this method creates a new
    resource that is a new version of the formally published resource. HydroShare will record the update by storing the
    SystemMetadata.obsoletes and SystemMetadata.obsoletedBy fields for the respective resources in their system metadata
    HydroShare MUST check or set the values of SystemMetadata.obsoletes and SystemMetadata.obsoletedBy so that they
    accurately represent the relationship between the new and old objects. HydroShare MUST also set
    SystemMetadata.dateSysMetadataModified. The modified system metadata entries must then be available in
    HydroShare.listObjects() to ensure that any cataloging systems pick up the changes when filtering on
    SystmeMetadata.dateSysMetadataModified. A formally published resource can only be obsoleted by one newer version.
    Once a resource is obsoleted, no other resources can obsolete it.

    """
    resource = utils.get_resource_by_shortkey(pk)
    ret = []
    for file in files:
        ret.append(ResourceFile.objects.create(
            content_object=resource,
            resource_file=File(file) if not isinstance(file, UploadedFile) else file
        ))
    return ret

def update_system_metadata(pk, **kwargs):
    """

    """
    return update_science_metadata(pk, **kwargs)


def update_science_metadata(pk, dublin_metadata=None, keywords=None, **kwargs):
    """
    Called by clients to update the science metadata for a resource in HydroShare.

    REST URL:  PUT /scimeta/{pid}

    Parameters:

    pid - Unique HydroShare identifier for the resource that is to be updated.

    ScienceMetadata - The data bytes of the ScienceMetadata that will update the existing Science Metadata for the resource
    identified by pid

    Returns:    The pid assigned to the resource whose Science Metadata was updated

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.InvalidContent - The content of the resource is incomplete
    Exception.ServiceFailure - The service is unable to process the request

    Notes:
    For mutable resources (resources that have not been formally published), the update overwrites existing Science
    Metadata using the ScienceMetadata that is passed to this method. For immutable resources (formally published
    resources), this method creates a new resource that is a new version of the formally published resource. HydroShare
    will record the update by storing the SystemMetadata.obsoletes and SystemMetadata.obsoletedBy fields for the
    respective resources in their system metadata. HydroShare MUST check or set the values of SystemMetadata.obsoletes
    and SystemMetadata.obsoletedBy so that they accurately represent the relationship between the new and old objects.
    hydroShare MUST also set SystemMetadata.dateSysMetadataModified. The modified system metadata entries must then be
    available in HydroShare.listObjects() to ensure that any cataloging systems pick up the changes when filtering on
    SystmeMetadata.dateSysMetadataModified. A formally published resource can only be obsoleted by one newer version.
    Once a resource is obsoleted, no other resources can obsolete it.

    """
    resource = utils.get_resource_by_shortkey(pk)

    if keywords:
        AssignedKeyword.objects.filter(content_object=resource).delete()
        ks = [Keyword.objects.get_or_create(k) for k in keywords]
        ks = zip(*ks)[0]  # ignore whether something was created or not.  zip is its own inverse

        for k in ks:
            AssignedKeyword.objects.create(content_object=resource, keyword=k)

    if dublin_metadata:
        QualifiedDublinCoreElement.objects.filter(content_object=resource).delete()
        for d in dublin_metadata:
            QualifiedDublinCoreElement.objects.create(
                term=d['term'],
                qualifier=d.get('qualifier'),
                content=d['content'],
                content_object=resource
            )

    if kwargs:
        for field, value in kwargs:
            setattr(resource, field, value)
        resource.save()

def delete_resource(pk):
    """
    Deletes a resource managed by HydroShare. The caller must be an owner of the resource or an administrator to perform
    this function. The operation removes the resource from further interaction with HydroShare services and interfaces. The
    implementation may delete the resource bytes, and should do so since a delete operation may be in response to a problem
    with the resource (e.g., it contains malicious content, is inappropriate, or is subject to a legal request). If the
    resource does not exist, the Exceptions.NotFound exception is raised.

    REST URL:  DELETE /resource/{pid}

    Parameters:
    pid - The unique HydroShare identifier of the resource to be deleted

    Returns:
    The pid of the resource that was deleted

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Note:  Only HydroShare administrators will be able to delete formally published resour
    """
    utils.get_resource_by_shortkey(pk).delete()
    return pk


def delete_resource_file(pk, filename):
    """
    Deletes an individual file from a HydroShare resource. If the file does not exist, the Exceptions.NotFound exception
    is raised.

    REST URL:  DELETE /resource/{pid}/files/{filename}

    Parameters:
    pid - The unique HydroShare identifier for the resource from which the file will be deleted
    filename - Name of the file to be deleted from the resource

    Returns:    The pid of the resource from which the file was deleted

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist or the file identified by file does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Note:  For mutable resources (resources that have not been formally published), this method modifies the resource by
    deleting the file. For immutable resources (formally published resources), this method creates a new resource that
    is a new version of the formally published resource. HydroShare will record the update by storing the
    SystemMetadata.obsoletes and SystemMetadata.obsoletedBy fields for the respective resources in their system metadata
    HydroShare MUST check or set the values of SystemMetadata.obsoletes and SystemMetadata.obsoletedBy so that they
    accurately represent the relationship between the new and old objects. HydroShare MUST also set
    SystemMetadata.dateSysMetadataModified. The modified system metadata entries must then be available in
    HydroShare.listObjects() to ensure that any cataloging systems pick up the changes when filtering on
    SystmeMetadata.dateSysMetadataModified. A formally published resource can only be obsoleted by one newer
    version. Once a resource is obsoleted, no other resources can obsolete it.
    """
    resource = utils.get_resource_by_shortkey(pk)
    for f in ResourceFile.objects.filter(content_object=resource):
        if f.resource_file.name == filename:
            f.resource_file.delete()
            f.delete()
            break
    else:
        raise ObjectDoesNotExist(filename)

    return filename


def publish_resource(pk):
    """
    Formally publishes a resource in HydroShare. Triggers the creation of a DOI for the resource, and triggers the
    exposure of the resource to the HydroShare DataONE Member Node. The user must be an owner of a resource or an
    adminstrator to perform this action.

    REST URL:  PUT /publishResource/{pid}

    Parameters:    pid - Unique HydroShare identifier for the resource to be formally published.

    Returns:    The pid of the resource that was published

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Note:  This is different than just giving public access to a resource via access control rul
    """
    resource = utils.get_resource_by_shortkey(pk)
    resource.published_and_frozen = True
    resource.frozen = True
    resource.edit_users = []
    resource.edit_groups = []
    resource.save()



def resolve_doi(doi):
    """
    Takes as input a DOI and returns the internal HydroShare identifier (pid) for a resource. This method will be used
    to get the HydroShare pid for a resource identified by a doi for further operations using the web service API.

    REST URL:  GET /resolveDOI/{doi}

    Parameters:    doi - A doi assigned to a resource in HydroShare.

    Returns:    The pid of the resource that was published

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Note:  All HydroShare methods (except this one) will use HydroShare internal identifiers (pids). This method exists
    so that a program can resolve the pid for a DOI.

    """
    return utils.get_resource_by_doi(doi).short_id