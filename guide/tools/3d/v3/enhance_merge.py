# Merge an AI-enhanced still back onto the exact Blender render:
# align AI -> render (ORB + homography), then paste the render's exact details through the mask.
import sys, cv2, numpy as np
render, ai, mask, out = sys.argv[1:5]
R = cv2.imread(render); A = cv2.imread(ai); M = cv2.imread(mask, cv2.IMREAD_UNCHANGED)
A = cv2.resize(A, (R.shape[1], R.shape[0]), interpolation=cv2.INTER_AREA)
g1, g2 = cv2.cvtColor(R, cv2.COLOR_BGR2GRAY), cv2.cvtColor(A, cv2.COLOR_BGR2GRAY)
orb = cv2.ORB_create(6000); k1, d1 = orb.detectAndCompute(g1, None); k2, d2 = orb.detectAndCompute(g2, None)
m = sorted(cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(d2, d1), key=lambda x: x.distance)[:800]
src = np.float32([k2[x.queryIdx].pt for x in m]); dst = np.float32([k1[x.trainIdx].pt for x in m])
H, inl = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
print("matches", len(m), "inliers", int(inl.sum()))
Aw = cv2.warpPerspective(A, H, (R.shape[1], R.shape[0]), borderMode=cv2.BORDER_REFLECT)
a = (M[:, :, 3] if M.shape[2] == 4 else cv2.cvtColor(M, cv2.COLOR_BGR2GRAY)).astype(np.float32) / 255
a = cv2.dilate(a, np.ones((7, 7), np.uint8)); a = cv2.GaussianBlur(a, (0, 0), 3)[..., None]
# match the render patch to the AI image's tone so the pasted details sit in the new light
Rf, Af = R.astype(np.float32), Aw.astype(np.float32)
w = a[..., 0] > 0.5
if w.sum() > 100:
    for c in range(3):
        rs, as_ = Rf[..., c][w], Af[..., c][w]
        Rf[..., c] = (Rf[..., c] - rs.mean()) * (as_.std() / (rs.std() + 1e-6)) ** 0.3 + as_.mean() * 0.35 + rs.mean() * 0.65
outimg = Af * (1 - a) + Rf * a
cv2.imwrite(out, np.clip(outimg, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 94])
