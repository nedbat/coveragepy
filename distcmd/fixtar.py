"""Add a 'fixtar' command to setup.py.

This lets us have proper permissions in tar files made on Windows.

"""
from distutils.core import Command
import shutil, tarfile

class fixtar(Command):
    """A new setup.py command to fix tar file permissions."""

    description = "Re-pack the tar file to have correct permissions."

    user_options = []

    def initialize_options(self):
        """Required by Command, even though I have nothing to add."""
        pass

    def finalize_options(self):
        """Required by Command, even though I have nothing to add."""
        pass

    def run(self):
        """The body of the command."""
        for _, _, filename in self.distribution.dist_files:
            if filename.endswith(".tar.gz"):
                self.repack_tar(filename, "temp.tar.gz")
                shutil.move("temp.tar.gz", filename)

    def repack_tar(self, infilename, outfilename):
        """Re-pack `infilename` as `outfilename`.

        Permissions and owners are set the way we like them.
        Also deletes the source directory, due to unfortunate setup.py
        mechanics.

        """
        itar = tarfile.open(infilename, "r:gz")
        otar = tarfile.open(outfilename, "w:gz")
        the_dir = None
        for itarinfo in itar:
            otarinfo = otar.gettarinfo(itarinfo.name)
            if the_dir is None:
                n = itarinfo.name
                assert n.count("/") == 1 and n.endswith("/")
                the_dir = n[:-1]
            if itarinfo.isfile():
                otarinfo.mode = 0644
            else:
                otarinfo.mode = 0755
            otarinfo.uid = 100
            otarinfo.gid = 100
            otarinfo.uname = "ned"
            otarinfo.gname = "coverage"
            otar.addfile(otarinfo, itar.extractfile(itarinfo))
        itar.close()
        otar.close()

        # To make this work, sdist has to be run with the --keep-temp option.
        # But the clean command doesn't clean up the temp directory.
        # Delete it here.
        shutil.rmtree(the_dir)
