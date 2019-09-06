#! /usr/bin/env python2
"""
License
--------------------------------------------------------------------------------
squirrel is released under version 3 of the GNU General Public License.

squirrel
Copyright (C) 2019  Bernhard VonZastrow

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import inspect
import os.path
import re
import shutil
import tempfile

try:
    import ix
except ImportError:
    ix = None

from bvzlib import config
from bvzlib import resources

from libClarisse import libClarisse
from libClarisse import libClarisseGui

from squirrel.gather import gather
from squirrel.librarian import librarian
from squirrel.shared.squirrelerror import SquirrelError

from clamerror import ClamError


# ==============================================================================
class Clam(object):

    """
    An object responsible for managing assets within clarisse. Relies on the
    Squirrel asset manager for actual asset management.
    """

    # --------------------------------------------------------------------------
    def __init__(self,
                 language="english"):
        """
        Initialize the object.

        :param language: The language used for communication with the end user.
               Defaults to "english".

        :return: Nothing.
        """

        self.language = language

        module_d = os.path.split(inspect.stack()[0][1])[0]
        resources_d = os.path.join(module_d, "..", "..", "resources")
        resources_d = os.path.abspath(resources_d)
        self.resc = resources.Resources(resources_d, "lib_clam", language)

        config_d = os.path.join(module_d, "..", "..", "config")
        config_d = os.path.abspath(config_d)
        self.config_p = os.path.join(config_d, "clam.config")
        self.config_obj = config.Config(self.config_p, "CLAM_CONFIG_PATH")

        self.validate_config()

        self.do_verified_copy = self.config_obj.getboolean("settings",
                                                           "do_verified_copy")

        self.librarian = librarian.Librarian(language)

    # --------------------------------------------------------------------------
    def validate_config(self):
        """
        Makes sure the config file is valid. Raises a squirrel error if not.

        :return: Nothing.
        """

        sections = dict()
        sections["settings"] = ["do_verified_copy"]

        failures = self.config_obj.validation_failures(sections)
        if failures:
            if failures[1] is None:
                err = self.resc.error(501)
                err.msg = err.msg.format(config_p=self.config_p,
                                         section=failures[0])
                raise ClamError(err.msg, err.code)
            else:
                err = self.resc.error(502)
                err.msg = err.msg.format(config_p=self.config_p,
                                         setting=failures[1],
                                         section=failures[0])
                raise ClamError(err.msg, err.code)

    # --------------------------------------------------------------------------
    def set_attributes(self):
        """
        Set up the instance.

        :return: Nothing.
        """

        pass

    # --------------------------------------------------------------------------
    @staticmethod
    def refs_in_project(project_p):
        """
        Given a path to a clarisse project, open that project's text file and
        extract all of the references to NON-clarisse files. We do this via a
        text file vs. built in clarisse api functions because it is MUCH easier
        this way (even if it is a bit janky).

        :param project_p: The path to the project we are testing.

        :return: A list of all the referenced files in this project.
        """

        assert os.path.exists(project_p)
        assert os.path.isfile(project_p)
        assert os.path.splitext(project_p)[1] == ".project"

        output = list()

        # \sfile(?:(?:name_open|name_save))? .*{\n\s*value "(.*)"
        # outer_pattern = '\h*(?:filename|filename_sys|)\s*(.*)\n'
        outer_pattern = r'\h*(?:filename|filename_sys|OSL_shader_filename|(?:(?:file|filename_open) .*{\n\s*value)) (".*")\n'
        inner_pattern = '"([^"]*)"'
        with open(project_p, "r") as f:
            lines = f.readlines()

        data = ""
        for line in lines:
            if line.startswith("#preferences"):
                break
            data += line

        references = re.findall(outer_pattern, data)

        if references:

            for ref in references:
                file_names = re.findall(inner_pattern, ref)
                for file_name in file_names:
                    file_name = libClarisse.pdir_to_path(file_name, project_p)
                    if not file_name.endswith(".project"):
                        output.append(file_name)

        return output

    # --------------------------------------------------------------------------
    def sub_projects_in_project_recursive(self,
                                          project_p):
        """
        Given a path to a clarisse project, open that project's text file and
        extract all of the other project tiles it references. We do this via a
        text file vs. build in clarisse api functions because it is MUCH easier
        this way (even if it is a bit janky).

        :param project_p: The path to the project we are testing.

        :return: A list of all the referenced sub-projects in this project.
        """

        assert os.path.exists(project_p)
        assert os.path.isfile(project_p)
        assert os.path.splitext(project_p)[1] == ".project"

        output = list()

        pattern = r'\h*(?:filename|filename_sys)\s*"(.*\.project)"\s*\n'
        with open(project_p, "r") as f:
            lines = f.readlines()

        data = ""
        for line in lines:
            if line.startswith("#preferences"):
                break
            data += line

        sub_projects = re.findall(pattern, data)

        if sub_projects:

            for sub_project in sub_projects:
                sub_project = libClarisse.pdir_to_path(sub_project, project_p)
                output.append(sub_project)
                output.extend(
                    self.sub_projects_in_project_recursive(sub_project))

        return output

    # --------------------------------------------------------------------------
    def all_refs_in_project_recursive(self,
                                      project_p):
        """
        Given a project, return a tuple of two lists: 1) All projects referenced
        in this or any sub-project, and 2) All other files referenced in this or
        any sub-project.

        :param project_p: A path to the project file we are testing.

        :return: A tuple where the first element is a list of all sub-projects
                 (recursively) and the second element is a list of all other,
                 non-project files referenced in any of these projects.
        """

        projects = self.sub_projects_in_project_recursive(project_p)
        projects = list(set(projects))

        references = self.refs_in_project(project_p)
        for sub_project_p in projects:
            references.extend(self.refs_in_project(sub_project_p))
        references = list(set(references))

        return projects, references

    # --------------------------------------------------------------------------
    @staticmethod
    def munge_project(project_p,
                      remapped,
                      relative=True):
        """
        Given a project, opens that project and does a text replace on any files
        to point to the new location. If relative is True, then the path will be
        converted to a relative path from source_p.

        :param project_p: The path to the project we are munging.
        :param remapped: The dictionary where the key is the original path that
               would be found in a project file, and the value is the path of
               where this file has been gathered to.
        :param relative: If True, then the munged path will be made relative to
               project we are munging. Defaults to True.

        :return: Nothing.
        """

        assert os.path.exists(project_p)
        assert os.path.isfile(project_p)
        assert os.path.splitext(project_p)[1] == ".project"
        assert type(remapped) is dict
        assert type(relative) is bool

        project_parent_d = os.path.split(project_p)[0]

        munged_p = project_p + ".out"

        with open(project_p, "r") as source_project_f:
            with open(munged_p, "w") as munged_project_f:
                line = source_project_f.readline()
                while line:
                    for key in remapped:
                        if key in line:
                            if relative:
                                rel_path = os.path.relpath(remapped[key],
                                                           project_parent_d)
                                rel_path = os.path.join("$PDIR", rel_path)
                                line = line.replace(key, rel_path)
                            else:
                                line = line.replace(key, remapped[key])
                    munged_project_f.write(line)
                    line = source_project_f.readline()

        shutil.copyfile(munged_p, project_p)
        os.remove(munged_p)

    # --------------------------------------------------------------------------
    def gather_project(self,
                       project_p,
                       dest,
                       skip_published=False,
                       repos=None):
        """
        Given a path to a clarisse project, open that project and recursively
        gather all the files referenced in this project or any of its
        references. We do this via a text file vs. built in clarisse api
        functions because it is MUCH easier this way (even if it is a bit
        janky).

        :param project_p: The path to the project we are gathering.
        :param dest: The destination where the context should be gathered to.
        :param skip_published: If True, then any files that are already being
               managed by the asset manager will not be gathered.
        :param repos: A list of repos to check if skip_published is True. If
               None, then all repos will be checked (if skip_published is True).
               Defaults to None.

        :return: The directory into which the project is gathered.
        """

        assert os.path.exists(project_p)
        assert os.path.isfile(project_p)
        assert os.path.splitext(project_p)[1] == ".project"
        assert os.path.exists(dest)
        assert os.path.isdir(dest)
        assert type(skip_published) is bool
        assert repos is None or type(repos) is list
        if repos:
            for repo in repos:
                assert type(repo) is str

        # Get every file (recursively) referenced in this project
        all_files = list()
        projects, refs = self.all_refs_in_project_recursive(project_p)
        all_files.extend(projects)
        all_files.extend(refs)
        all_files.append(project_p)

        # Create a gather object and remap the files
        gather_obj = gather.Gather(self.language)
        gather_obj.set_attributes(
            files=all_files,
            dest=dest,
            mapping=None,
            padding=None,
            udim_identifier="<UDIM>",
            strict_udim_format=True,
            match_hash_length=False)
        gather_obj.remap_files()

        # If skip_published, remove any files that are already published
        if skip_published:

            if not repos:
                repo_names = None
                check_all_repos = True
            else:
                repo_names = repos
                check_all_repos = False

            librarian_obj = librarian.Librarian()

            files_to_cull = list()
            for source_p in gather_obj.remapped:
                if librarian_obj.file_is_within_repo(source_p,
                                                     repo_names,
                                                     check_all_repos):
                    files_to_cull.append(source_p)

            for file_to_cull in files_to_cull:
                gather_obj.cull_file(file_to_cull)

        # Actually copy the files to their remap location
        gather_obj.copy_files(verbose=True)

        copied_files_p = list()
        for file_p in gather_obj.remapped:
            copied_files_p.append(gather_obj.remapped[file_p])

        for file_p in copied_files_p:
            if file_p.endswith(".project"):
                self.munge_project(file_p, gather_obj.remapped, True)

    # --------------------------------------------------------------------------
    def gather_context(self,
                       context,
                       dest):
        """
        Given a context, gather all of the files in it (and any referenced
        contexts).

        :param context: The context we want to gather.
        :param dest: The destination where the context should be gathered to.
               This should be a directory, inside of which the asset directory
               will be created (i.e. the individual files will be gathered into
               a sub-dir inside this dir that is named the same as the context).

        :return: The directory where the context was gathered. I.e. the sub-dir
                 of dest that is the gathered context.
        """

        assert(context.is_context())
        assert(os.path.exists(dest))
        assert(os.path.isdir(dest))

        if not libClarisse.contexts_are_atomic(context):
            err = self.resc.error(102)
            err.msg = err.msg.format(context=context.get_name())
            raise ClamError(err.msg, err.code)

        # Create a temporary, exported project
        temp_project_dir = tempfile.mkdtemp(prefix="temp_project_")
        exported_p = libClarisse.export_context_with_deps(context,
                                                          temp_project_dir,
                                                          True)
        dest = os.path.join(dest, context.get_name())
        if not os.path.exists(dest):
            os.mkdir(dest)
        self.gather_project(exported_p, dest)

        os.remove(exported_p)

        return dest

    # --------------------------------------------------------------------------
    def publish_context(self,
                        context,
                        repo=None):
        """
        Given a context, gather all of the files in it (and any referenced
        contexts) to a temp location. Then publish these files to the publishing
        back end.

        :param context: The context we want to gather.
        :param repo: The repository to publish to. If None, then the default
               repository will be used. Defaults to None.

        :return: The directory where the context was gathered.
        """

        assert(context.is_context())
        assert repo is None or (type(repo) is str and repo)

        if not libClarisse.contexts_are_atomic(context):
            raise ClamError("Context is not atomic", 1001)

        asset_name = context.get_name()

        try:
            self.librarian.validate_name(asset_name, repo)
        except SquirrelError as err:
            raise ClamError(err.message, err.code)

        gather_parent_d = self.librarian.get_gather_loc()
        gather_parent_d = tempfile.mkdtemp(dir=gather_parent_d)
        gathered_loc = self.gather_context(context, gather_parent_d)

        token = self.librarian.extract_token_from_name(context.get_name(), repo)
        pub_loc = self.librarian.get_publish_loc(token, repo)

        self.librarian.store(name=asset_name,
                             asset_parent_d=pub_loc,
                             src_p=gathered_loc,
                             metadata=None,
                             keywords=None,
                             notes=None,
                             thumbnails=None,
                             poster_frame=None,
                             merge=True,
                             pins=None,
                             verify_copy=self.do_verified_copy)

        # TODO: Delete the gather_loc
        # TODO: return the path to the published project
        return "ljh" # <-- this should be the path to the published project

    # --------------------------------------------------------------------------
    def publish_context_as_ref(self,
                               context,
                               repo=None):
        """
        Given a context, gather all of the files in it (and any referenced
        contexts) to a temp location. Then publish these files to publishing
        back end. Replace the context with a reference to the published project.

        :param context: The context we want to gather.
        :param repo: The back end repository to publish to. If None, then the
               default repository will be used. Defaults to None.

        :return: The directory where the context was gathered.
        """

        assert(context.is_context())

        if not libClarisse.contexts_are_atomic(context):
            raise ClamError("Context is not atomic", 1001)

        published_project = self.publish_context(context, repo)

        # TODO: Replace local context with a reference to the published project

    # ---------------------------------------------------------------------------
    def failed_name_validations(self,
                                names,
                                repo):
        """
        Given a list of asset names, returns None if all of the names are valid.
        Returns a dictionary if any of the names are not valid). The key is the
        name that is not valid, and the value is a string describing how the
        name is not valid.

        :param names: A list of asset names (in string format).
        :param repo: The name of the repo to validate against.

        :return: None if all of the names are valid. If any are invalid, returns
                 a dictionary where the keys are any names that are not valid
                 and the values are the reasons why the names are not valid.
        """

        assert type(names) is list
        for name in names:
            assert type(name) is str
        assert type(repo) is str and repo != ""

        failed = dict()
        for name in names:
            try:
                self.librarian.validate_name(name, repo)
            except SquirrelError as e:
                failed[name] = e.message

        if not failed:
            return None
        return failed

    # --------------------------------------------------------------------------
    def validate_context_names(self,
                               contexts,
                               repo=None,
                               display_success=False):
        """
        Validates a list of names against the given repo. If no repo is give,
        then the default repo will be used. Failures will be displayed to the
        user.

        :param contexts: A list of asset names (in string format).
        :param repo: The name of the repo to validate against. If None, then the
               default repo will be used. Defaults to None.
        :param display_success: If True, a dialog showing success will be
               displayed. If False, then a success will not display any info to
               the user. Defaults to False.

        :return: Nothing.
        """

        assert type(contexts) is list
        for context in contexts:
            assert context.is_context()
        assert repo is None or (type(repo) is str and repo != "")
        assert type(display_success) is bool

        if not repo:
            repo = self.librarian.get_default_repo()

        names = list()
        for context in contexts:
            names.append(context.get_name())

        failed = self.failed_name_validations(names, repo)
        if failed:
            title = self.resc.message("failed_name_title")
            body = self.resc.message("failed_name_body")
            for failure in failed:
                body += "\n   --> " + failure + "  -  " + failed[failure]
            libClarisseGui.display_error_dialog(body, title)
            return False

        if not failed:
            if display_success:
                title = self.resc.message("success_title")
                body = self.resc.message("success_body")
                libClarisseGui.display_message_dialog(body, title)
            return True

        return False

    # --------------------------------------------------------------------------
    def selection_to_context_list(self):
        """
        Takes in the selection and returns a list of contexts.

        :return:
        """

        items = libClarisse.clarisse_array_to_python_list(ix.selection)
        contexts = list()
        for item in items:
            if item.is_context():
                contexts.append(item)

        if not contexts:
            title = self.resc.message("no_contexts_title")
            body = self.resc.message("no_contexts_body")
            libClarisseGui.display_error_dialog(body, title)
            return None

        return contexts

    # --------------------------------------------------------------------------------------------------
    def create_empty_asset_structure(self,
                                     name,
                                     parent_context=None,
                                     existing_geo=None):
        """
        Create a new asset context in Clarisse. This context will have
        sub-contexts and combiners, groups, and shading layers in it that define
        a standard asset structure.

        :param name: The name of the asset. This will be vetted against the
               librarian to see if it is a valid name.
        :param parent_context: The context into which the new asset will be
               created. If None, then it will be created at the root of the
               project.
        :param existing_geo: If given as a context or item, this will move the
               context (or item) into the geo sub-context. If None, nothing
               happens. Defaults to None.

        :return: Nothing
        """

        assert type(name) is str and name
        assert parent_context is None or parent_context.is_context()

        self.librarian.validate_name(name)

        if not parent_context:
            context_url = r"project:/"
        else:
            context_url = parent_context.get_full_name().rstrip("/")

        asset_url = "/".join([context_url, name])
        geo_url = "/".join([asset_url, "geo"])
        shading_url = "/".join([asset_url, "shading"])
        maps_url = "/".join([shading_url, "maps"])
        support_url = "/".join([shading_url, "support"])
        shaders_url = "/".join([shading_url, "shaders"])

        asset_context = libClarisse.create_context(asset_url)
        libClarisse.create_context(geo_url)

        libClarisse.create_context(shading_url)
        libClarisse.create_context(maps_url)
        libClarisse.create_context(support_url)
        libClarisse.create_context(shaders_url)

        if existing_geo:
            ix.cmds.MoveItemTo(existing_geo.get_full_name(), geo_url)

        geo_group = ix.cmds.CreateObject("geo_gr", "Group", "Global", geo_url)
        ix.cmds.SetValues([geo_group.get_full_name() + ".inclusion_rule[0]"],
                          ["./*"])
        ix.cmds.SetValues([geo_group.get_full_name() + ".exclusion_rule[0]"],
                          ["*_HDN*"])

        material = ix.cmds.CreateObject(name + "_MAT",
                                        "MaterialPhysicalStandard",
                                        shaders_url)

        out_combiner = ix.cmds.CreateObject(name + "_OUT",
                                            "SceneObjectCombiner",
                                            "Global",
                                            asset_url)
        ix.cmds.AddValues([out_combiner.get_full_name() + ".objects"],
                          [geo_group.get_full_name()])

        shading_layer = ix.cmds.CreateObject(name + "_sl",
                                             "ShadingLayer",
                                             "Global",
                                             asset_url)

        ix.cmds.SetShadingLayerRulesProperty(shading_layer.get_full_name(),
                                             [0],
                                             "filter",
                                             ["*/" + name + "/geo/*"])

        ix.cmds.SetShadingLayerRulesProperty(shading_layer.get_full_name(),
                                             [0], "material",
                                             [material.get_full_name()])

        return asset_context
