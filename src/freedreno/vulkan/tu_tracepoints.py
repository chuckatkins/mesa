#
# Copyright © 2021 Igalia S.L.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice (including the next
# paragraph) shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import argparse
import sys

#
# TODO can we do this with less boilerplate?
#
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--import-path', required=True)
parser.add_argument('--utrace-src', required=True)
parser.add_argument('--utrace-hdr', required=True)
parser.add_argument('--perfetto-hdr', required=True)
args = parser.parse_args()
sys.path.insert(0, args.import_path)


from u_trace import Header, HeaderScope
from u_trace import ForwardDecl
from u_trace import Tracepoint
from u_trace import TracepointArg as Arg
from u_trace import TracepointArgStruct as ArgStruct
from u_trace import utrace_generate
from u_trace import utrace_generate_perfetto_utils

# List of the default tracepoints enabled. By default tracepoints are enabled,
# set tp_default_enabled=False to disable them by default.
tu_default_tps = []

#
# Tracepoint definitions:
#

Header('util/u_dump.h')
Header('vk_format.h')
Header('freedreno/vulkan/tu_private.h', scope=HeaderScope.SOURCE)

ForwardDecl('struct tu_device')


def begin_end_tp(name, args=[], tp_struct=None, tp_print=None,
                 tp_default_enabled=True):
    global tu_default_tps
    if tp_default_enabled:
        tu_default_tps.append(name)
    Tracepoint('start_{0}'.format(name),
               toggle_name=name,
               tp_perfetto='tu_start_{0}'.format(name))
    Tracepoint('end_{0}'.format(name),
               toggle_name=name,
               args=args,
               tp_struct=tp_struct,
               tp_perfetto='tu_end_{0}'.format(name),
               tp_print=tp_print)


begin_end_tp('render_pass',
    args=[ArgStruct(type='const struct tu_framebuffer *', var='fb')],
    tp_struct=[Arg(type='uint16_t', name='width',        var='fb->width',                                    c_format='%u'),
               Arg(type='uint16_t', name='height',       var='fb->height',                                   c_format='%u'),
               Arg(type='uint8_t',  name='MRTs',         var='fb->attachment_count',                         c_format='%u'),
            #    Arg(type='uint8_t',  name='samples',      var='fb->samples',                                  c_format='%u'),
               Arg(type='uint16_t', name='numberOfBins', var='fb->tile_count.width * fb->tile_count.height', c_format='%u'),
               Arg(type='uint16_t', name='binWidth',     var='fb->tile0.width',                              c_format='%u'),
               Arg(type='uint16_t', name='binHeight',    var='fb->tile0.height',                             c_format='%u')])

begin_end_tp('binning_ib')
begin_end_tp('draw_ib_sysmem')
begin_end_tp('draw_ib_gmem')

begin_end_tp('gmem_clear',
    args=[Arg(type='enum VkFormat',  var='format',  c_format='%s', to_prim_type='vk_format_description({})->short_name'),
          Arg(type='uint8_t',        var='samples', c_format='%u')])

begin_end_tp('sysmem_clear',
    args=[Arg(type='enum VkFormat',  var='format',      c_format='%s', to_prim_type='vk_format_description({})->short_name'),
          Arg(type='uint8_t',        var='uses_3d_ops', c_format='%u'),
          Arg(type='uint8_t',        var='samples',     c_format='%u')])

begin_end_tp('sysmem_clear_all',
    args=[Arg(type='uint8_t',        var='mrt_count',   c_format='%u'),
          Arg(type='uint8_t',        var='rect_count',  c_format='%u')])

begin_end_tp('gmem_load',
    args=[Arg(type='enum VkFormat',  var='format',   c_format='%s', to_prim_type='vk_format_description({})->short_name'),
          Arg(type='uint8_t',        var='force_load', c_format='%u')])

begin_end_tp('gmem_store',
    args=[Arg(type='enum VkFormat',  var='format',   c_format='%s', to_prim_type='vk_format_description({})->short_name'),
          Arg(type='uint8_t',        var='fast_path', c_format='%u'),
          Arg(type='uint8_t',        var='unaligned', c_format='%u')])

begin_end_tp('sysmem_resolve',
    args=[Arg(type='enum VkFormat',  var='format',   c_format='%s', to_prim_type='vk_format_description({})->short_name')])

begin_end_tp('blit',
    # TODO: add source megapixels count and target megapixels count arguments
    args=[Arg(type='uint8_t',        var='uses_3d_blit', c_format='%u'),
          Arg(type='enum VkFormat',  var='src_format',   c_format='%s', to_prim_type='vk_format_description({})->short_name'),
          Arg(type='enum VkFormat',  var='dst_format',   c_format='%s', to_prim_type='vk_format_description({})->short_name'),
          Arg(type='uint8_t',        var='layers',       c_format='%u')])

begin_end_tp('compute',
    args=[Arg(type='uint8_t',  var='indirect',       c_format='%u'),
          Arg(type='uint16_t', var='local_size_x',   c_format='%u'),
          Arg(type='uint16_t', var='local_size_y',   c_format='%u'),
          Arg(type='uint16_t', var='local_size_z',   c_format='%u'),
          Arg(type='uint16_t', var='num_groups_x',   c_format='%u'),
          Arg(type='uint16_t', var='num_groups_y',   c_format='%u'),
          Arg(type='uint16_t', var='num_groups_z',   c_format='%u')])

utrace_generate(cpath=args.utrace_src,
                hpath=args.utrace_hdr,
                ctx_param='struct tu_device *dev',
                trace_toggle_name='tu_gpu_tracepoint',
                trace_toggle_defaults=tu_default_tps)
utrace_generate_perfetto_utils(hpath=args.perfetto_hdr)
