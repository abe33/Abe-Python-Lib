# -*- coding: utf-8 -*-

PAIN_PREFIX = '.pain%s'
PAIN_BLOCK_PREFIX = '.block'
PAIN_AFFECTED_PREFIX = '.affected'
PAIN_KILLER_PREFIX = '.killer'
PAIN_DONE_PREFIX = '.done'

PAIN_COLOR = 0x999999
PAIN_BLOCK_COLOR = 0xf6aa16
PAIN_AFFECTED_COLOR = 0x1b8bb5
PAIN_KILLER_COLOR = 0xf12b16
PAIN_DONE_COLOR = 0x9ACD32

r_base = 255
g_base = 255
b_base = 255

def print_style(color,style_name):
    i = 0
    l = 100
    r = 0
    g = 0
    b = 0
    css = ''
    while( i <= l ):
        ref_r = 255-( color >> 16 & 0xff )
        ref_g = 255-( color >> 8 & 0xff )
        ref_b = 255-( color & 0xff )
        r = ( 255 - int(i*ref_r / 100) ) << 16
        g = ( 255 - int(i*ref_g /100) ) << 8
        b = ( 255 - int(i*ref_b / 100) )
        css = ( style_name % i ) + '{ background:' + hex( int( r + g + b  ) ).replace( '0x', '#' ) + '; }'
        print(css)
        i=i+1
    print('')
    
print_style( PAIN_COLOR, PAIN_PREFIX )
print_style( PAIN_BLOCK_COLOR, PAIN_PREFIX + PAIN_BLOCK_PREFIX )
print_style( PAIN_KILLER_COLOR, PAIN_PREFIX+ PAIN_BLOCK_PREFIX + PAIN_KILLER_PREFIX )
print_style( PAIN_AFFECTED_COLOR, PAIN_PREFIX  + PAIN_BLOCK_PREFIX + PAIN_AFFECTED_PREFIX )
print_style( PAIN_DONE_COLOR, PAIN_PREFIX  + PAIN_DONE_PREFIX )
