// Test-only Shell.Eval probe for a disposable GNOME session. Adds 25 ms controlled repaint load.
(async()=>{
 const GLib=(await import('gi://GLib')).default;
 const ext=Main.extensionManager.lookup('fliqlo-ubuntu@luan-thnh').stateObj;
 const delay=ms=>new Promise(resolve=>GLib.timeout_add(GLib.PRIORITY_DEFAULT,ms,()=>{resolve();return GLib.SOURCE_REMOVE;}));
 Main.overview.hide();ext._settings.set_boolean('idle-enabled',false);ext._settings.set_boolean('flip-animation',true);
 await delay(300);ext._settings.set_int('preview-token',(ext._settings.get_int('preview-token')+1)%2147483647);await delay(200);
 if(!ext._root)throw Error('screensaver overlay did not open');
 const phase=()=>ext._progress ?? (ext._started?Math.min(1,(GLib.get_monotonic_time()-ext._started)/330000):1);
 const presented=[],drawn=[]; let lastDrawn=1; const addedPaintLoadMs=25;
 const id=global.stage.connect('after-paint',()=>{if(ext._previous)presented.push(lastDrawn);});
 for(const area of ext._areas)area.connect('repaint',()=>{lastDrawn=phase();drawn.push(lastDrawn);const until=GLib.get_monotonic_time()+addedPaintLoadMs*1000;while(GLib.get_monotonic_time()<until){};});
 ext._current={...ext._current,minutes:String((new Date().getMinutes()+59)%60).padStart(2,'0')};
 await delay(1600);
 global.stage.disconnect(id);ext._hide();
 const intermediate=[...new Set(presented.filter(v=>v>0&&v<1))];
 return {shell:Config.PACKAGE_VERSION,backend:'headless Wayland, software renderer',addedPaintLoadMs,drawn,presented,distinctIntermediatePresented:intermediate.length,overlayClosed:!ext._root};
})()
