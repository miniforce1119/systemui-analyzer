"""
회사 regression 시스템 다운로드 파일과 동일한 구조의 테스트 데이터 생성

생성 구조:
  test_downloads/
  ├── S948NKSU2AZDD_ram_000_20260421_220306.zip
  ├── S948NKSU2AZDD_ram_001_20260421_221430.zip
  ├── S948NKSU2AZDD_ram_002_20260421_222500.zip
  ├── S948NKSU2AZDD_ram_000_20260421_220306.png  (더미)
  ├── S948NKSU2AZDE_ram_000_20260422_224025.zip
  ├── S948NKSU2AZDE_ram_001_20260422_225149.zip
  ├── S948NKSU2AZDE_ram_002_20260422_230313.zip
  ├── S948NKSU2AZDE_ram_000_20260422_224025.png  (더미)
  └── S948NKSU2AZDE_rom_000_20260422_224004.zip  (더미)

각 zip 내부:
  ├── dumpsys_meminfo_all   ← SystemUI 포함 전체 프로세스 상세
  ├── dumpsys_meminfo       ← 전체 프로세스 간략 PSS 목록
  ├── boot_stat
  ├── features
  └── property
"""

import zipfile
import random
from pathlib import Path


def generate_meminfo_section(pid, process, pss_base, native_base, dalvik_base,
                              graphics_base, views_base, activities=0, variation=0):
    """개별 프로세스의 meminfo 섹션 생성"""
    v = lambda base: base + random.randint(-variation, variation)

    native = v(native_base)
    dalvik = v(dalvik_base)
    dalvik_other = v(3456)
    stack = v(512)
    so_mmap = v(8234)
    art_mmap = v(3456)
    egl = v(8192)
    gl = v(graphics_base)
    unknown = v(2345)

    total_pss = native + dalvik + dalvik_other + stack + so_mmap + art_mmap + egl + gl + unknown
    total_rss = int(total_pss * 1.25)

    java_heap_pss = int(dalvik * 1.15)
    code_pss = so_mmap + v(3000)
    graphics_pss = egl + gl
    private_other = dalvik_other + unknown
    system_pss = v(3686)

    return f"""** MEMINFO in pid {pid} [{process}] **
                   Pss  Private  Private  SwapPss      Rss     Heap     Heap     Heap
                 Total    Dirty    Clean      Dirty    Total     Size    Alloc     Free
                ------   ------   ------   ------   ------   ------   ------   ------
  Native Heap    {native}    {native-100}      120       45    {int(native*1.1)}    32768    {native+1000}     8534
  Dalvik Heap    {dalvik}    {dalvik-150}      100       30    {int(dalvik*1.07)}    40960    {dalvik+2000}     8504
 Dalvik Other     {dalvik_other}     {dalvik_other-50}       50        0     {dalvik_other+500}
        Stack      {stack}      {stack}        0        0      {stack+80}
     .so mmap     {so_mmap}      400     5200       20    15000
    .art mmap     {art_mmap}     3200      100       10     5000
   EGL mtrack     {egl}     {egl}        0        0     {egl}
  GL mtrack    {gl}    {gl}        0        0    {gl}
    Unknown     {unknown}     {unknown-100}      100       15     {unknown+600}
        TOTAL    {total_pss}    {int(total_pss*0.81)}    {int(total_pss*0.15)}      120   {total_rss}    73728    40690    17038

 App Summary
                       Pss(KB)                        Rss(KB)
                        Total                          Total
                   ------                         ------
           Java Heap:    {java_heap_pss}                         {int(java_heap_pss*1.12)}
         Native Heap:    {native}                         {int(native*1.1)}
                Code:    {code_pss}                         {code_pss+15000}
               Stack:      {stack}                           {stack+80}
            Graphics:    {graphics_pss}                         {graphics_pss}
       Private Other:     {private_other}
              System:     {system_pss}
             TOTAL PSS:    {total_pss}              TOTAL RSS:   {total_rss}

 Objects
               Views:      {v(views_base)}          ViewRootImpl:        3
         AppContexts:       12           Activities:        {activities}
              Assets:       15        AssetManagers:        5
       Local Binders:      {v(234)}       Proxy Binders:       {v(89)}
       Parcel memory:       56         Parcel count:       34
    Death Recipients:       23      OpenSSL Sockets:        0
            WebViews:        0

 SQL
         MEMORY_USED:      345
  PAGECACHE_OVERFLOW:       12          MALLOC_SIZE:       62

 DATABASES
      pgsz     dbsz   Lookaside(b)          cache  Dbname
         4       48             32         2/16/4  /data/user_de/0/com.android.systemui/databases/notification_log.db
         4       24             28         1/12/3  /data/user_de/0/com.android.systemui/databases/peopledb.db
         4       16             20         0/8/2   /data/user_de/0/com.android.systemui/databases/smartspace.db
"""


def generate_meminfo_all(version_type="normal"):
    """dumpsys_meminfo_all 전체 파일 생성

    version_type: "normal" (정상) 또는 "regression" (메모리 증가)
    """
    header = "Applications Memory Usage (in Kilobytes):\nUptime: 629155 Realtime: 629155\n\n"

    if version_type == "normal":
        systemui = generate_meminfo_section(
            pid=4603, process="com.android.systemui",
            pss_base=84000, native_base=15234, dalvik_base=22456,
            graphics_base=12288, views_base=456, activities=0, variation=200
        )
    else:
        # regression: 메모리 대폭 증가
        systemui = generate_meminfo_section(
            pid=4603, process="com.android.systemui",
            pss_base=126000, native_base=25890, dalvik_base=38912,
            graphics_base=18432, views_base=823, activities=2, variation=300
        )

    # 다른 프로세스들 (고정)
    system_server = generate_meminfo_section(
        pid=1000, process="system_server",
        pss_base=200000, native_base=50000, dalvik_base=80000,
        graphics_base=5000, views_base=100, variation=100
    )

    launcher = generate_meminfo_section(
        pid=5188, process="com.sec.android.app.launcher",
        pss_base=60000, native_base=20000, dalvik_base=15000,
        graphics_base=10000, views_base=200, variation=100
    )

    return header + system_server + "\n" + systemui + "\n" + launcher


def generate_meminfo_summary():
    """dumpsys_meminfo (전체 프로세스 간략 PSS 목록)"""
    return """Total RSS by process:
  545,616K: system (pid 1000)
  319,872K: com.android.systemui (pid 4603)
  217,384K: com.sec.android.app.launcher (pid 5188)
  175,840K: com.android.phone (pid 4376)
  162,532K: com.google.android.gms (pid 7111)
  148,204K: com.samsung.android.app.spage (pid 14257)
"""


def create_zip(output_path, version_type="normal"):
    """실제 회사 zip과 동일한 구조의 파일 생성"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("dumpsys_meminfo_all", generate_meminfo_all(version_type))
        zf.writestr("dumpsys_meminfo", generate_meminfo_summary())
        zf.writestr("boot_stat", "Boot completed in 12345ms")
        zf.writestr("features", "android.hardware.bluetooth\nandroid.hardware.camera")
        zf.writestr("property", "ro.build.display.id=S948NKSU2AZDE\nro.build.type=user")


def main():
    output_dir = Path("test_downloads")
    output_dir.mkdir(exist_ok=True)

    random.seed(42)  # 재현 가능한 결과

    # 버전 A (정상 - baseline): S948NKSU2AZDD, 3회 테스트
    for i, (date, time) in enumerate([
        ("20260421", "220306"),
        ("20260421", "221430"),
        ("20260421", "222500"),
    ]):
        filename = f"S948NKSU2AZDD_ram_{i:03d}_{date}_{time}.zip"
        create_zip(output_dir / filename, version_type="normal")
        print(f"  생성: {filename}")

    # 버전 B (regression - 메모리 증가): S948NKSU2AZDE, 3회 테스트
    for i, (date, time) in enumerate([
        ("20260422", "224025"),
        ("20260422", "225149"),
        ("20260422", "230313"),
    ]):
        filename = f"S948NKSU2AZDE_ram_{i:03d}_{date}_{time}.zip"
        create_zip(output_dir / filename, version_type="regression")
        print(f"  생성: {filename}")

    # 더미 파일들 (무시되어야 함)
    (output_dir / "S948NKSU2AZDE_ram_000_20260422_224025.png").write_bytes(b"dummy png")
    (output_dir / "S948NKSU2AZDE_rom_000_20260422_224004.zip").write_bytes(b"dummy rom")
    print("  생성: 더미 파일 (png, rom)")

    print(f"\n테스트 데이터 생성 완료: {output_dir}/")
    print(f"총 {len(list(output_dir.glob('*.zip')))} zip + {len(list(output_dir.glob('*.png')))} png")


if __name__ == "__main__":
    main()
