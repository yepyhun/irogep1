"""
Windows Sandbox .wsb profil generátor (MVP).
Nem indít sandboxot, csak a profil XML szövegét állítja elő.
"""
from __future__ import annotations
import sys, html
from datetime import datetime, timezone
import time

sys.dont_write_bytecode = True

def _xml_bool(value: bool) -> str:
    return "Disable" if value else "Enable"

def make_wsb_xml(src_ro: str, work_dir: str, out_dir: str, *, disable_net: bool=True, disable_vgpu: bool=True) -> str:
    """
    Állítson elő egy .wsb XML profilt a Windows Sandbox számára.

    :param src_ro: Hoston lévő forrás mappa, melyet RO-ként csatolunk, és a sandboxban ugyanarra az elérési útra tükrözünk.
    :param work_dir: Írható munkakönyvtár (host és sandbox oldali ugyanarra a pathra tükrözve).
    :param out_dir: Írható kimeneti könyvtár (host és sandbox oldali ugyanarra a pathra tükrözve).
    :param disable_net: Ha True, a sandboxban a hálózat letiltva.
    :param disable_vgpu: Ha True, a sandboxban a vGPU letiltva.
    :return: A .wsb fájl XML tartalma (string).
    """
    # Meta: időbélyeg (UTC) és mért idő az előállításhoz
    t0 = time.monotonic()
    ts = datetime.now(timezone.utc).isoformat()

    # Biztonság kedvéért escape-eljük az útvonalakat
    s_src = html.escape(src_ro)
    s_work = html.escape(work_dir)
    s_out = html.escape(out_dir)

    xml = f"""<Configuration>
  <VGpu>{_xml_bool(disable_vgpu)}</VGpu>
  <Networking>{_xml_bool(disable_net)}</Networking>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>{s_src}</HostFolder>
      <SandboxFolder>{s_src}</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
    <MappedFolder>
      <HostFolder>{s_work}</HostFolder>
      <SandboxFolder>{s_work}</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
    <MappedFolder>
      <HostFolder>{s_out}</HostFolder>
      <SandboxFolder>{s_out}</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>cmd /c echo Sandbox ready at {ts}</Command>
  </LogonCommand>
</Configuration>"""
    _ = time.monotonic() - t0  # mért idő (MVP: nem használjuk fel, de jelen van)
    return xml
