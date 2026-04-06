import optparse
import os
import sys
import shutil
import platform

# Setup paths
script_dir = os.path.dirname(__file__)
root_dir = os.path.abspath(script_dir)
curl_root = os.path.join(root_dir, 'curl')

# Add gyp-next to path
sys.path.insert(0, os.path.join(root_dir, 'build', 'gyp-next', 'pylib'))

try:
    import gyp
except ImportError:
    print('You need to install gyp in build/gyp-next first. See the README.')
    sys.exit(42)

def host_arch():
    machine = platform.machine()
    if machine == 'i386':
        return 'ia32'
    return 'x64'

def configure_defines(o, options):
    """Configures libcurl defines"""
    target = options.target_arch if options.target_arch else host_arch()
    o.extend(['-D', f'target_arch={target}'])
    o.extend(['-D', f'host_arch={host_arch()}'])
    o.extend(['-D', 'library=static_library'])

def configure_buildsystem(o, options):
    """Configures buildsystem paths and files"""
    # Define architecture-specific output path
    rel_out_dir = os.path.join('out', options.target_arch)
    abs_out_dir = os.path.join(root_dir, rel_out_dir)

    # Ensure output directory exists to prevent gyp-next from dumping in root
    os.makedirs(abs_out_dir, exist_ok=True)

    # GYP Flags
    o.append('curl.gyp')
    o.extend(['-I', 'common.gypi'])
    o.extend(['-f', 'msvs'])

    if options.toolchain and options.toolchain != 'auto':
        o.extend(['-G', f'msvs_version={options.toolchain}'])

    o.append('--depth=.')
    o.append(f'--generator-output={rel_out_dir}')
    o.append(f'-Goutput_dir={rel_out_dir}')
    o.append(f'--suffix=.{options.target_arch}')

    # Copy required headers/sources
    # Format: (src_folder, src_file, dest_sub1, dest_sub2, dest_file)
    files_to_copy = [
        ("build", "curlbuild.h", "include", "curl", "curlbuild.h"),
        ("build", "tool_hugehelp.c", "lib", "", "tool_hugehelp.c")
    ]

    for src_sub, src_file, dst_sub1, dst_sub2, dst_file in files_to_copy:
        src = os.path.join(root_dir, src_sub, src_file)
        # os.path.join handles the empty string gracefully for the second file
        dst = os.path.join(curl_root, dst_sub1, dst_sub2, dst_file)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src, dst)

def run_gyp(args):
    """Executes gyp from the root directory"""
    os.chdir(root_dir)
    rc = gyp.main(args)
    if rc != 0:
        print('Error running GYP')
        sys.exit(rc)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("--toolchain", dest="toolchain", type='choice',
                      choices=['2008', '2010', '2012', '2013', 'auto'], default='auto')
    parser.add_option("--target-arch", dest="target_arch", type='choice',
                      choices=['x86', 'x64'], default='x86')

    (options, _) = parser.parse_args()

    # Collect all arguments into a single list
    gyp_args = []
    configure_buildsystem(gyp_args, options)
    configure_defines(gyp_args, options)

    run_gyp(gyp_args)
