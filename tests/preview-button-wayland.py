"""Optional integration test; requires an isolated GNOME session with the test Eval helper."""
import sys,json,os
from pathlib import Path
sys.path.insert(0,os.environ.get('FLIQLO_TEST_APP_DIR',str(Path(__file__).resolve().parents[1]/'native')))
import app
from gi.repository import Gtk,Gio,GLib
application=app.App();application.register(None)
config=app.settings()
assert app.extension_info().get('state')==1
window=app.Preferences(application,config)
window.preview(None)
Gio.Settings.sync()
errors=[]
def check():
 try:
  bus=Gio.bus_get_sync(Gio.BusType.SESSION,None)
  opened=bus.call_sync('org.gnome.Shell','/org/gnome/Shell','org.gnome.Shell','Eval',
   GLib.Variant('(s)',("Boolean(Main.extensionManager.lookup('fliqlo-ubuntu@luan-thnh').stateObj._root)",)),
   GLib.VariantType.new('(bs)'),Gio.DBusCallFlags.NONE,3000,None).unpack()
  assert opened==(True,'true'),opened
  code=Path(__file__).with_name('gnome-presentation.js').read_text()
  result=bus.call_sync('org.gnome.Shell','/org/gnome/Shell','org.gnome.Shell','Eval',
   GLib.Variant('(s)',(code,)),GLib.VariantType.new('(bs)'),Gio.DBusCallFlags.NONE,10000,None).unpack()
  assert result[0],result
  report=json.loads(result[1]);report['entryPoint']='Actual Preferences.preview GTK handler with active GNOME extension'
  assert report['distinctIntermediatePresented']>=2,report
  print(json.dumps(report))
 except Exception as error:errors.append(error)
 window.destroy();Gtk.main_quit()
 return GLib.SOURCE_REMOVE
GLib.timeout_add(500,check)
Gtk.main()
if errors:raise errors[0]
