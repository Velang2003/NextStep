import { useState, useEffect, memo } from 'react';
import AppLayout from '../components/AppLayout';
import api from '../services/api';
import { ComposableMap, Geographies, Geography, ZoomableGroup } from 'react-simple-maps';
import { scaleLinear } from 'd3-scale';
import { Globe, Layers, MapPin, Search, Maximize2, Loader2, Sparkles, Target, Compass } from 'lucide-react';

const GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json';

// Refined Professional Color Range for Map
const COLOR_RANGE = ['#1e1b4b', '#312e81', '#4338ca', '#6366f1', '#818cf8', '#a5b4fc'];

const MapChart = memo(({ geoData, maxCount, onHover, onLeave }) => {
  const colorScale = scaleLinear()
    .domain([0, maxCount * 0.1, maxCount * 0.3, maxCount * 0.5, maxCount * 0.75, maxCount])
    .range(COLOR_RANGE);

  const dataMap = {};
  geoData.forEach(g => {
    if (g.country) dataMap[g.country.toLowerCase()] = g;
    if (g.iso3) dataMap[g.iso3.toLowerCase()] = g;
  });
  if (dataMap['united states']) dataMap['united states of america'] = dataMap['united states'];
  if (dataMap['uk']) dataMap['united kingdom'] = dataMap['uk'];
  if (dataMap['south korea']) dataMap['korea'] = dataMap['south korea'];

  return (
    <ComposableMap
      projection="geoMercator"
      projectionConfig={{ scale: 130, center: [10, 20] }}
      style={{ width: '100%', height: '100%' }}
    >
      <ZoomableGroup>
        <Geographies geography={GEO_URL}>
          {({ geographies }) =>
            geographies.map(geo => {
              const name = geo.properties?.name || geo.properties?.NAME || '';
              const iso3 = geo.properties?.ISO_A3 || geo.id || '';
              const gd = dataMap[name.toLowerCase()] || dataMap[iso3.toLowerCase()];
              const count = gd ? gd.count : 0;
              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  onMouseEnter={() => onHover(geo, count, gd)}
                  onMouseLeave={onLeave}
                  style={{
                    default: {
                      fill: count > 0 ? colorScale(count) : 'var(--color-subtle)',
                      stroke: 'var(--color-base)',
                      strokeWidth: 0.5,
                      outline: 'none',
                    },
                    hover: {
                      fill: count > 0 ? 'var(--color-primary)' : 'var(--color-base)',
                      stroke: 'var(--color-primary)',
                      strokeWidth: 1,
                      outline: 'none',
                      cursor: 'pointer',
                    },
                  }}
                />
              );
            })
          }
        </Geographies>
      </ZoomableGroup>
    </ComposableMap>
  );
});

MapChart.displayName = 'MapChart';

export default function GeoMap() {
  const [geoData, setGeoData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tooltip, setTooltip] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    api.get('/jobs/trends/geo')
      .then(r => setGeoData(r.data || []))
      .catch(() => { })
      .finally(() => setLoading(false));
  }, []);

  const maxCount = Math.max(...geoData.map(g => g.count), 1);
  const totalJobs = geoData.reduce((sum, g) => sum + g.count, 0);

  const handleHover = (geo, count, gd) => {
    const name = geo.properties?.name || geo.properties?.NAME || 'Unknown';
    setTooltip({
      name,
      count,
      country: gd?.country || name,
      role: gd?.dominant_role,
      skill: gd?.dominant_skill,
      sector: gd?.dominant_sector
    });
  };

  const handleMouseMove = (e) => {
    let x = e.clientX + 15;
    let y = e.clientY - 30;
    if (typeof window !== 'undefined') {
      if (x + 280 > window.innerWidth) x = e.clientX - 280;
      if (y + 220 > window.innerHeight) y = e.clientY - 220;
      if (y < 10) y = 10;
    }
    setTooltipPos({ x, y });
  };

  return (
    <AppLayout>
      <div className="space-y-10 max-w-7xl mx-auto">
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-[0.2em]">
              <Globe className="w-3.5 h-3.5" />
              Job Map
            </div>
            <h1 className="text-4xl font-black font-outfit text-main">Jobs by Location</h1>
            <p className="text-muted text-lg font-medium">See where the most jobs are located across {geoData.length} countries.</p>
          </div>
          
          <div className="flex gap-4">
            <div className="flex items-center gap-4 bg-subtle px-6 py-3 rounded-2xl border border-base">
              <Compass className="w-5 h-5 text-primary" />
              <div className="flex flex-col">
                <span className="text-[10px] font-black text-muted uppercase tracking-widest">Total Locations</span>
                <span className="text-sm font-bold text-main">{geoData.length} Countries</span>
              </div>
            </div>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { label: 'Analyzed Countries', value: geoData.length, icon: Globe, color: 'text-primary' },
            { label: 'Total Openings', value: totalJobs.toLocaleString(), icon: Layers, color: 'text-secondary' },
            { label: 'Top Location', value: geoData[0]?.country || '—', icon: Target, color: 'text-success' },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="surface-card p-8 flex items-center gap-6">
              <div className={`w-14 h-14 rounded-2xl bg-subtle border border-base flex items-center justify-center ${color}`}>
                <Icon className="w-7 h-7" />
              </div>
              <div className="space-y-1">
                <p className="text-[10px] font-black text-muted uppercase tracking-widest">{label}</p>
                <p className="text-3xl font-black font-outfit text-main">{value}</p>
              </div>
            </div>
          ))}
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-40 space-y-4 surface-card">
            <Loader2 className="w-10 h-10 text-primary animate-spin" />
            <p className="text-muted font-bold uppercase tracking-widest text-xs">Loading map data...</p>
          </div>
        ) : (
          <div className="space-y-8 animate-in-slide">
            {/* Map Canvas */}
            <div className="surface-card p-4 lg:p-8 relative group overflow-hidden" onMouseMove={handleMouseMove}>
              <div className="absolute top-8 right-8 z-10 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="w-10 h-10 rounded-xl bg-surface border border-base shadow-lg flex items-center justify-center text-muted hover:text-primary hover:border-primary/30 transition-all">
                  <Maximize2 className="w-4 h-4" />
                </button>
                <button className="w-10 h-10 rounded-xl bg-surface border border-base shadow-lg flex items-center justify-center text-muted hover:text-primary hover:border-primary/30 transition-all">
                  <Search className="w-4 h-4" />
                </button>
              </div>

              <div className="h-[600px] w-full bg-subtle/30 rounded-3xl border border-dashed border-base/50">
                <MapChart
                  geoData={geoData}
                  maxCount={maxCount}
                  onHover={handleHover}
                  onLeave={() => setTooltip(null)}
                />
              </div>

              {/* Enhanced Tooltip */}
              {tooltip && (
                <div
                  className="fixed z-50 surface-card p-5 border-primary/20 pointer-events-none w-[280px] shadow-2xl backdrop-blur-xl bg-surface/95 rounded-2xl animate-in-fade"
                  style={{
                    left: 0,
                    top: 0,
                    transform: `translate3d(${tooltipPos.x}px, ${tooltipPos.y}px, 0)`,
                    willChange: 'transform'
                  }}
                >
                  <div className="flex items-center justify-between mb-4 border-b border-base pb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-primary" />
                      <span className="text-main font-black font-outfit text-base tracking-tight">{tooltip.name}</span>
                    </div>
                    <span className="bg-primary/10 text-primary font-black text-xs px-2.5 py-1 rounded-lg border border-primary/20">
                      {tooltip.count > 0 ? tooltip.count : '0'} Jobs
                    </span>
                  </div>
                  <div className="space-y-4">
                    {tooltip.count > 0 ? (
                      <>
                        {[
                          { label: 'Dominant Role', value: tooltip.role, icon: Sparkles, color: 'text-primary' },
                          { label: 'Top Skill', value: tooltip.skill, icon: Target, color: 'text-secondary' },
                          { label: 'Primary Sector', value: tooltip.sector, icon: MapPin, color: 'text-success' },
                        ].map(({ label, value, icon: Icon, color }) => (
                          <div key={label} className="flex items-start gap-3">
                            <Icon className={`w-3.5 h-3.5 mt-0.5 ${color}`} />
                            <div className="flex flex-col">
                              <span className="text-[9px] font-black text-muted uppercase tracking-widest">{label}</span>
                              <span className="text-xs font-bold text-main truncate max-w-[180px]">{value || 'N/A'}</span>
                            </div>
                          </div>
                        ))}
                      </>
                    ) : (
                      <div className="py-4 text-center">
                        <p className="text-muted text-xs italic font-medium">Insufficient data for this region</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Legend Overlay */}
              <div className="absolute bottom-10 left-10 surface-card px-5 py-4 border-primary/10 bg-surface/80 backdrop-blur-md">
                <p className="text-[10px] font-black text-muted uppercase tracking-[0.2em] mb-3">Number of Jobs</p>
                <div className="flex items-center gap-1 mb-2">
                  {COLOR_RANGE.map((color, i) => (
                    <div key={i} className="w-8 h-2.5 rounded-full" style={{ background: color }} />
                  ))}
                </div>
                <div className="flex justify-between text-[10px] font-black text-muted/60 px-0.5">
                  <span>Fewer Jobs</span>
                  <span>More Jobs</span>
                </div>
              </div>
            </div>

            {/* Detailed Distribution Table */}
            <div className="grid grid-cols-1 lg:grid-cols-1 gap-8">
              <div className="surface-card p-10 space-y-8">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold font-outfit text-main flex items-center gap-3">
                    <Search className="w-6 h-6 text-primary" />
                    Job Distribution
                  </h2>
                  <span className="text-xs font-black text-muted uppercase tracking-widest">Top 15 Hubs</span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6">
                  {geoData.slice(0, 15).map((loc, i) => {
                    const pct = Math.round(loc.count / maxCount * 100);
                    return (
                      <div key={loc.country} className="space-y-2 group">
                        <div className="flex justify-between items-end">
                          <div className="flex items-center gap-4">
                            <span className="text-xs font-black text-muted/40 w-4">{i + 1}</span>
                            <span className="text-sm font-bold text-main group-hover:text-primary transition-colors">{loc.country}</span>
                          </div>
                          <span className="text-xs font-black text-main">{loc.count.toLocaleString()} <span className="text-muted/60">Jobs</span></span>
                        </div>
                        <div className="h-2 bg-subtle rounded-full overflow-hidden border border-base">
                          <div 
                            className="h-full rounded-full bg-gradient-to-r from-primary to-secondary transition-all duration-1000 ease-out"
                            style={{ width: `${pct}%` }} 
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}

