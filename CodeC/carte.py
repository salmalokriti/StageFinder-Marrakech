"""Cartes HTML : Leaflet (colorée, sans clé) et Google Maps (avec clé)."""
import json

COULEURS = ["#123B66", "#d03b3b", "#1F9D6B", "#F59E0B", "#7C3AED", "#0891B2", "#DB2777", "#65A30D"]
CENTRE = {"lat": 31.6295, "lng": -7.9811}


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def preparer(df, couleurs_par_domaine):
    """Liste de dicts prête pour le JavaScript (coordonnées EXACTES du fichier)."""
    out = []
    for r in df.to_dict("records"):
        out.append({
            "nom": r["Entreprise"], "domaine": r["Domaine"], "adresse": r["Adresse"],
            "lat": float(r["Latitude"]), "lng": float(r["Longitude"]),
            "couleur": couleurs_par_domaine.get(r["Domaine"], "#123B66"),
            "maps": r["Google Maps"], "itineraire": r["Itinéraire"],
            "linkedin": r["LinkedIn (entreprise)"], "offres": r["Offres Google"],
        })
    return out


_POPUP_JS = """
function esc(s){const d=document.createElement('div');d.textContent=s==null?'':s;return d.innerHTML;}
function popup(d){
  const b='display:inline-block;margin:3px 4px 0 0;padding:5px 10px;border-radius:8px;font-size:12px;'
         +'font-weight:600;text-decoration:none;color:#fff;';
  return '<div style="font-family:Inter,Arial,sans-serif;min-width:230px;max-width:270px">'
    +'<div style="font-size:11px;font-weight:700;color:'+d.couleur+';text-transform:uppercase">'+esc(d.domaine)+'</div>'
    +'<div style="font-size:16px;font-weight:800;color:#14213D;margin:2px 0 4px">'+esc(d.nom)+'</div>'
    +'<div style="font-size:12px;color:#555;margin-bottom:6px">📍 '+esc(d.adresse)+'</div>'
    +'<a target="_blank" style="'+b+'background:#123B66" href="'+encodeURI(d.maps)+'">Google Maps</a>'
    +'<a target="_blank" style="'+b+'background:#1F9D6B" href="'+encodeURI(d.itineraire)+'">Itinéraire</a>'
    +'<a target="_blank" style="'+b+'background:#0A66C2" href="'+encodeURI(d.linkedin)+'">LinkedIn</a>'
    +'<a target="_blank" style="'+b+'background:#d03b3b" href="'+encodeURI(d.offres)+'">Offres</a></div>';
}
"""

_LEGENDE_CSS = """
.legende{background:#fff;padding:10px 14px;border-radius:12px;box-shadow:0 4px 14px rgba(0,0,0,.2);
 font:12px Inter,Arial,sans-serif;line-height:1.9;color:#14213D}
.legende i{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:7px}
.pin{width:26px;height:26px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:3px solid #fff;
 box-shadow:0 3px 8px rgba(0,0,0,.45);position:relative}
.pin::after{content:'';position:absolute;width:8px;height:8px;border-radius:50%;background:#fff;top:6px;left:6px}
"""


def html_leaflet(marqueurs, focus=None, hauteur=640):
    focus_js = _json(focus) if focus is not None else "null"
    return f"""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>html,body{{margin:0}}#map{{height:{hauteur}px;border-radius:16px}}{_LEGENDE_CSS}</style>
<div id="map"></div>
<script>
const DATA={_json(marqueurs)}; const FOCUS={focus_js};
{_POPUP_JS}
const plan=L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',
  {{maxZoom:20,attribution:'© OpenStreetMap © CARTO'}});
const sat=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{maxZoom:19,attribution:'Tiles © Esri'}});
const map=L.map('map',{{layers:[plan]}}).setView([{CENTRE['lat']},{CENTRE['lng']}],13);
L.control.layers({{'🗺️ Plan':plan,'🛰️ Satellite':sat}},null,{{position:'topright'}}).addTo(map);
const pts=[];let focusMarker=null;
DATA.forEach((d,i)=>{{
  const icon=L.divIcon({{className:'',html:'<div class="pin" style="background:'+d.couleur+'"></div>',
    iconSize:[26,26],iconAnchor:[4,26],popupAnchor:[9,-24]}});
  const m=L.marker([d.lat,d.lng],{{icon,title:d.nom}}).addTo(map).bindPopup(popup(d));
  pts.push([d.lat,d.lng]); if(FOCUS!==null&&i===FOCUS) focusMarker=m;
}});
if(focusMarker){{map.setView(focusMarker.getLatLng(),17);focusMarker.openPopup();}}
else if(pts.length){{map.fitBounds(pts,{{padding:[40,40]}});}}
const dom={{}};DATA.forEach(d=>dom[d.domaine]=d.couleur);
const leg=L.control({{position:'bottomleft'}});
leg.onAdd=()=>{{const el=L.DomUtil.create('div','legende');
  el.innerHTML='<b>Secteurs</b><br>'+Object.entries(dom).map(([n,c])=>'<i style="background:'+c+'"></i>'+esc(n)).join('<br>');
  return el;}};
leg.addTo(map);
</script>"""


def html_google(marqueurs, cle, focus=None, hauteur=640):
    focus_js = _json(focus) if focus is not None else "null"
    return f"""
<style>html,body{{margin:0}}#map{{height:{hauteur}px;border-radius:16px}}
#err{{display:none;font:14px Arial;padding:16px;background:#fff3cd;border-radius:12px}}</style>
<div id="err">⚠️ Google Maps a refusé la clé (API « Maps JavaScript API » non activée, facturation absente
ou restriction de référent). Utilisez le mode « Plan coloré » en attendant.</div>
<div id="map"></div>
<script>
const DATA={_json(marqueurs)}; const FOCUS={focus_js};
{_POPUP_JS}
window.gm_authFailure=()=>{{document.getElementById('err').style.display='block';
  document.getElementById('map').style.display='none';}};
function initMap(){{
  const map=new google.maps.Map(document.getElementById('map'),
    {{center:{_json(CENTRE)},zoom:13,mapTypeControl:true,streetViewControl:false}});
  const info=new google.maps.InfoWindow();const bounds=new google.maps.LatLngBounds();
  DATA.forEach((d,i)=>{{
    const pos={{lat:d.lat,lng:d.lng}};
    const m=new google.maps.Marker({{position:pos,map,title:d.nom,animation:google.maps.Animation.DROP,
      icon:{{path:'M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24s12-15 12-24C24 5.4 18.6 0 12 0z',
        fillColor:d.couleur,fillOpacity:1,strokeColor:'#fff',strokeWeight:2,scale:1,
        anchor:new google.maps.Point(12,36)}}}});
    const ouvrir=()=>{{info.setContent(popup(d));info.open(map,m);}};
    m.addListener('click',ouvrir); bounds.extend(pos);
    if(FOCUS===i){{map.setCenter(pos);map.setZoom(17);ouvrir();}}
  }});
  if(FOCUS===null&&DATA.length) map.fitBounds(bounds);
}}
</script>
<script async src="https://maps.googleapis.com/maps/api/js?key={cle}&callback=initMap"></script>"""
