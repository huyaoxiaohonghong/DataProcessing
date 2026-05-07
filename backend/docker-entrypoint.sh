#!/usr/bin/env bash
# 鍚姩鍏ュ彛鑴氭湰
# - 浠?root 韬唤淇鍛藉悕鍗?(backend_media / backend_logs) 鐨勬墍鏈夋潈
#   (docker 棣栨鎸傝浇绌哄嵎鏃朵細缁ф壙闀滃儚鐩綍鎵€鏈夋潈, 浣嗗凡瀛樺湪鐨勫嵎鎵€鏈夋潈浼氫繚鐣?
#    闇€瑕佹瘡娆″惎鍔ㄦ椂鍏滃簳 chown)
# - 鐒跺悗鍒囨崲鍒?appuser 鎵ц搴旂敤
set -e

# 淇濊瘉鍏抽敭鐩綍瀛樺湪骞跺綊灞?appuser
for d in /app/media /app/media/uploads /app/media/processing_results /app/logs; do
    mkdir -p "$d"
done

# 浠呭湪浠?root 杩愯鏃舵墠 chown (鏈€缁堥暅鍍忎細浣跨敤 gosu 鍒囨崲鐢ㄦ埛)
if [ "$(id -u)" = "0" ]; then
    chown -R appuser:appuser /app/media /app/logs || true
    exec gosu appuser "$@"
else
    exec "$@"
fi
