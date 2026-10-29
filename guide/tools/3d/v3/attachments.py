# Attachments for model v3 (photos 053 whisk, 054 beater, 055 hook, 007 blender jar, 021/048 meat grinder).
# Executed inside build_mixer3.py after the machine is built; uses its helpers (tube, cyl, lathe, box, slab, mat...).
# Each builder takes the collar point (top of the tool, where it meets the shaft) and returns the objects it made.

def collar(name, x, y, z, disc=0.0):
    objs = [cyl(name + "_collar", 1.2, 2.2, (x, y, z - 1.1), material=STEEL, verts=48, bev=0.2)]
    if disc: objs.append(cyl(name + "_disc", disc, 0.15, (x, y, z - 2.3), material=STEEL, verts=96))
    return objs

def make_whisk(x, y, z, wires=12):
    # balloon whisk: 4 loops (8 wires) in vertical planes, teardrop profile 16 cm long, 11 cm wide
    objs = collar("whisk", x, y, z) + [cyl("whisk_ferrule", 0.9, 1.6, (x, y, z - 2.9), material=STEEL, verts=32)]
    L = 15.5
    def r_of(t):  # t 0 (collar) .. 1 (tip): wide balloon, almost round, widest at 60 %, rounded tip (owner's note, photo 053)
        R, c = 7.4, 0.6
        if t < c: return 0.6 + (R - 0.6) * math.sin(math.pi / 2 * t / c) ** 0.7
        return R * math.sqrt(max(0.0, 1 - ((t - c) / (1 - c)) ** 2))
    for k in range(wires // 2):
        a = math.pi * k / (wires // 2)
        pts = []
        for i in range(61):
            s = i / 60  # 0..1 down one side, then up the other
            t = s * 2 if s <= 0.5 else (1 - s) * 2
            side = 1 if s <= 0.5 else -1
            rr = r_of(t) * side
            pts.append((x + rr * math.cos(a), y + rr * math.sin(a), z - 3.6 - L * t))
        objs.append(tube(f"whisk_wire{k}", pts, 0.11, material=STEEL))
    return objs

def make_beater(x, y, z):
    # flat beater: shield-shaped frame with two ribs, cast aluminium look (photo 054)
    objs = collar("beater", x, y, z, disc=3.4)
    H, Wd = 15.0, 6.2
    frame = []
    for i in range(73):
        a = math.tau * i / 72
        # shield: wide rounded bottom, narrowing to the neck at the top
        px = Wd * math.sin(a) * (0.55 + 0.45 * (1 - math.cos(a)) / 2)
        pz = -H * (1 - math.cos(a)) / 2
        frame.append((x + px, y, z - 2.6 + pz))
    objs.append(tube("beater_frame", frame, 0.5, material=SATIN))
    objs.append(tube("beater_neck", [(x, y, z - 2.0), (x, y, z - 3.2)], 0.7, material=SATIN))
    def fp(deg):  # point on the frame at parameter angle deg
        a = math.radians(deg)
        return (x + Wd * math.sin(a) * (0.55 + 0.45 * (1 - math.cos(a)) / 2), y, z - 2.6 - H * (1 - math.cos(a)) / 2)
    spine = [(x, y, z - 2.6 - H * f) for f in (0.0, 0.25, 0.5, 0.72)]
    objs.append(tube("beater_spine", spine, 0.4, material=SATIN))
    # two ribs from the spine to the right side of the frame, one to the left (photo 054)
    for k, (f, deg) in enumerate(((0.25, 75), (0.5, 120), (0.38, -100))):
        p0 = (x, y, z - 2.6 - H * f); p1 = fp(deg)
        mid = ((p0[0] + p1[0]) / 2, y, (p0[2] + p1[2]) / 2 - 0.8)
        objs.append(tube(f"beater_rib{k}", [p0, mid, p1], 0.36, material=SATIN))
    return objs

def make_hook(x, y, z):
    objs = collar("hook", x, y, z, disc=3.6)
    hk = []
    for k in range(31):
        t = k / 30
        hk.append((x + 2.2 * math.sin(math.pi * t * 0.9) + 0.8 * t, y + 0.6 * math.sin(math.pi * t), z - 2.3 - 15.5 * t))
    hk += [(hk[-1][0] + 1.2, y + 0.2, hk[-1][2] - 0.5), (hk[-1][0] + 2.6, y, hk[-1][2] - 0.4)]
    objs.append(tube("hook_bar", hk, 0.68, material=STEEL))
    return objs

def make_blender(x, y, ztop):
    # blender jar standing on the rear top port: black base collar, clear faceted jar, handle, black lid with cap
    BLK = mat("blk", (0.02, 0.02, 0.022), rough=0.35, coat=0.3)
    objs = [lathe("bl_base", [(5.6, 0), (6.4, 0.3), (6.6, 3.6), (6.2, 4.2), (5.6, 4.3)], (x, y, ztop), material=BLK, thick=0, sub=1)]
    objs.append(lathe("bl_jar", [(5.4, 4.2), (6.3, 6.5), (7.0, 14), (7.6, 22), (7.9, 25.5), (8.0, 25.8)], (x, y, ztop), material=CLEAR, thick=0.35, sub=1))
    objs.append(lathe("bl_lid", [(0.01, 26.9), (6.0, 26.8), (8.1, 26.2), (8.2, 25.6)], (x, y, ztop), material=BLK, thick=0.3, sub=1))
    objs.append(cyl("bl_cap", 1.6, 1.6, (x, y, ztop + 27.6), material=BLK, verts=48, bev=0.2))
    objs.append(cyl("bl_blade_hub", 1.0, 1.4, (x, y, ztop + 5.0), material=STEEL, verts=32))
    for k in range(4):
        a = math.pi / 2 * k
        b = box(f"bl_blade{k}", (3.2, 0.9, 0.08), (x + 1.6 * math.cos(a), y + 1.6 * math.sin(a), ztop + 5.6 + 0.3 * (k % 2)), material=STEEL)
        b.rotation_euler = (math.radians(12 if k % 2 else -12), 0, a); objs.append(b)
    hp = [(x + 7.2, y, ztop + 22.5), (x + 11.0, y, ztop + 21.5), (x + 11.8, y, ztop + 17), (x + 11.2, y, ztop + 9.5), (x + 6.8, y, ztop + 8.5)]
    objs.append(tube("bl_handle", hp, 0.9, material=CLEAR))
    return objs

def make_grinder(x, z):
    # meat grinder in the head-end port (x = port face), auger body along -X, feed tube up, tray, ring nut + plate
    objs = [cyl("gr_coupler", 3.0, 2.4, (x - 1.2, 0, z), rot=(0, math.radians(90), 0), material=SATIN, verts=64, bev=0.3)]
    objs.append(cyl("gr_body", 3.3, 11.0, (x - 7.8, 0, z - 0.8), rot=(0, math.radians(90), 0), material=SATIN, verts=64, bev=0.3))
    objs.append(cyl("gr_ring", 4.2, 1.8, (x - 14.0, 0, z - 0.8), rot=(0, math.radians(90), 0), material=SATIN, verts=64, bev=0.5))
    for k in range(4):  # ring-nut lugs
        a = math.pi / 2 * k + math.pi / 4
        objs.append(box(f"gr_lug{k}", (1.6, 1.2, 1.2), (x - 14.0, 4.4 * math.cos(a), z - 0.8 + 4.4 * math.sin(a)), material=SATIN, bev=0.3))
    objs.append(cyl("gr_plate", 3.6, 0.3, (x - 15.0, 0, z - 0.8), rot=(0, math.radians(90), 0), material=STEEL, verts=64))
    objs.append(cyl("gr_feed", 2.4, 9.0, (x - 6.8, 0, z + 4.5), material=SATIN, verts=48, bev=0.3))
    tr = slab("gr_tray", rounded_poly([(x - 14.5, -6.0), (x + 0.5, -6.0), (x + 0.5, 6.0), (x - 14.5, 6.0)], [1.5] * 4), z + 9.0, z + 9.5, 0.2, material=STEEL)
    objs.append(tr)
    objs.append(lathe("gr_tray_rim", [(0.01, 0), (0.01, 0)], (0, 0, 0), material=STEEL, thick=0, sub=0))
    objs.append(cyl("gr_pusher", 1.9, 9.0, (x - 6.8, 0, z + 12.0), material=mat("pblk", (0.02, 0.02, 0.022), rough=0.5), verts=48, bev=0.3))
    return objs
