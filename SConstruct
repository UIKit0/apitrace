#############################################################################
#
# Copyright 2008 Tungsten Graphics, Inc.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import os
import os.path
import sys

opts = Options('config.py')
opts.Add(BoolOption('debug', 'build debug version', 'no'))
opts.Add(PathOption('dxsdk', 'DirectX SDK installation dir', os.environ.get('DXSDK_DIR', 'C:\\DXSDK')))
opts.Add(EnumOption('MSVS_VERSION', 'Microsoft Visual Studio version', None, allowed_values=('7.1', '8.0', '9.0')))

env = Environment(
    options = opts, 
    ENV = os.environ)
Help(opts.GenerateHelpText(env))

env.Append(CPPDEFINES = [
    'WIN32', 
    '_WINDOWS', 
    '_UNICODE',
    'UNICODE',
    '_CRT_SECURE_NO_DEPRECATE',
    '_CRT_NON_CONFORMING_SWPRINTFS',
    'WIN32_LEAN_AND_MEAN',
    '_USRDLL',
    ('_WIN32_WINNT', '0x0501'), # minimum required OS version
])

if env['debug']:
    env.Append(CPPDEFINES = ['_DEBUG'])
else:
    env.Append(CPPDEFINES = ['NDEBUG'])
env['PDB'] = '${TARGET.base}.pdb'

cflags = [
    '/W4', # warning level
]
if env['debug']:
    cflags += [
      '/Od', # disable optimizations
      '/Oy-', # disable frame pointer omission
    ]
else:
    cflags += [
      '/Ox', # maximum optimizations
      '/Os', # favor code space
    ]
cflags += [
    '/Oi', # enable intrinsic functions
    '/GF', # enable read-only string pooling
    '/MT',
]
env.Append(CFLAGS = cflags)
env.Append(CXXFLAGS = cflags)

env.Prepend(LIBS = [
    'kernel32',
    'user32',
    'gdi32',
])

Export('env')
SConscript('zlib/SConscript')

env.Append(CPPPATH = [
    os.path.join(env['dxsdk'], 'Include'),
])

conf = Configure(env)
has_d3d9 = conf.CheckCHeader('d3d9.h')
has_d3d8 = conf.CheckCHeader('d3d8.h')
has_d3d7 = conf.CheckCHeader('ddraw.h')
env = conf.Finish()

if has_d3d7:
    env.Command(
        target = 'ddraw.cpp', 
        source = ['ddraw.py', 'd3d.py', 'd3dtypes.py', 'd3dcaps.py', 'windows.py', 'base.py'],
        action = 'python $SOURCE > $TARGET',
    )
        
    ddraw = env.SharedLibrary(
        target = 'ddraw',
        source = [
            'ddraw.def',
            'ddraw.cpp',
            'log.cpp',
        ]
    )

    env.Default(ddraw)

if has_d3d8:
    env.Command(
        target = 'd3d8.cpp', 
        source = ['d3d8.py', 'd3d8types.py', 'd3d8caps.py', 'windows.py', 'base.py'],
        action = 'python $SOURCE > $TARGET',
    )
        
    d3d8 = env.SharedLibrary(
        target = 'd3d8',
        source = [
            'd3d8.def',
            'd3d8.cpp',
            'log.cpp',
        ]
    )

    env.Default(d3d8)

if has_d3d9:
    env.Command(
        target = 'd3d9.cpp', 
        source = ['d3d9.py', 'd3d9types.py', 'd3d9caps.py', 'windows.py', 'base.py'],
        action = 'python $SOURCE > $TARGET',
    )
        
    d3d9 = env.SharedLibrary(
        target = 'd3d9',
        source = [
            'd3d9.def',
            'd3d9.cpp',
            'log.cpp',
        ]
    )

    env.Default(d3d9)

env.Command(
    target = 'opengl32.cpp', 
    source = ['opengl32.py', 'gl.py', 'windows.py', 'base.py'],
    action = 'python $SOURCE > $TARGET',
)
    
opengl32 = env.SharedLibrary(
    target = 'opengl32',
    source = [
        'opengl32.def',
        'opengl32.cpp',
        'log.cpp',
    ]
)

env.Default(opengl32)

env.Tool('packaging')

zip = env.Package(
    NAME           = 'apitrace',
    VERSION        = '0.3',
    PACKAGEVERSION = 0,
    PACKAGETYPE    = 'zip',
    LICENSE        = 'lgpl',
    SUMMARY        = 'Tool to trace Direct3D & OpenGL API calls from applications.',
    SOURCE_URL     = 'http://cgit.freedesktop.org/~jrfonseca/apitrace/',
    source = [
        'README',
        'COPYING',
        'COPYING.LESSER',
        'd3d8.dll',
        'd3d9.dll',
        'apitrace.xsl',
        'apitrace.css',
        'xml2txt.py',
    ],
)

env.Alias('zip', zip)
