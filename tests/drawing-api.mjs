// Only a drawing-contract stub; image comparisons use real Pango/Cairo instead.
class FontDescription { set_family() {} set_weight() {} set_absolute_size() {} }
class LinearGradient {addColorStopRGB() {}}
class ImageSurface {finish() {}}
class Context {constructor() {return new Proxy({}, {get: () => () => {}});}}
export const api = {LinearGradient, ImageSurface, Context, Format: {ARGB32: 0}, Operator: {ADD: 12},
    Pango: {SCALE: 1024, FontDescription, Weight: {BOLD: 700, NORMAL: 400}},
    PangoCairo: {create_layout: () => ({set_font_description() {}, set_text() {}, get_size: () => [540*1024,600*1024], get_baseline: () => 444*1024}), show_layout() {}},
};
