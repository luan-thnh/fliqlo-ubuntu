// Optional real GJS/Pango/Cairo check; pass the scratch directory from compare-reference.
import Cairo from 'cairo';
import GLib from 'gi://GLib';
import Pango from 'gi://Pango';
import PangoCairo from 'gi://PangoCairo';
import {parts, paint} from '../extension/clock.js';
const directory = ARGV[0];
let cases;
if (directory) {
    const [,bytes] = GLib.file_get_contents(`${directory}/cases.json`);
    cases = JSON.parse(new TextDecoder().decode(bytes));
} else {
    cases = [.2,.75].map(progress => ({width:1350,height:700,hour:12,minute:0,previous:{hour:11,minute:59},progress,format:0,scale:100,brightness:100,background:true}));
}
const api = {LinearGradient:Cairo.LinearGradient,Operator:Cairo.Operator,
    ImageSurface:Cairo.ImageSurface,Format:Cairo.Format,Context:Cairo.Context,Pango,PangoCairo};
for (let i=0;i<cases.length;i++) {
    const c=cases[i], surface=new Cairo.ImageSurface(Cairo.Format.ARGB32,c.width,c.height), cr=new Cairo.Context(surface);
    const current=parts(new Date(2026,0,1,c.hour,c.minute),c.format);
    const previous=c.previous?parts(new Date(2026,0,1,c.previous.hour,c.previous.minute),c.format):null;
    paint(cr,c.width,c.height,current,previous,c.progress??1,
        {scale:c.scale,brightness:c.brightness,background:c.background,font:directory?'Fliqlo Bold':'DejaVu Sans'},api);
    if (directory) surface.writeToPNG(`${directory}/gjs-${i}.png`);cr.$dispose();surface.finish();
}
// Verify the custom flip card and digit palettes render in the actual GJS engine.
{
    const surface = new Cairo.ImageSurface(Cairo.Format.ARGB32, 1024, 576);
    const cr = new Cairo.Context(surface);
    paint(cr, 1024, 576, parts(new Date(2026,0,1,9,41),0),
        null, 1, {scale:100,brightness:100,background:true,
                  font:'DejaVu Sans',flapColorsEnabled:true,
                  flapBackgroundColor:'#173a56',flapDigitColor:'#d5f1ff'}, api);
    cr.$dispose();
    surface.finish();
}
print(`${cases.length} real GJS renderer frames plus custom color palette passed.`);
