# Valkyria Chronicles 2 (PSP) — 한글패치 기술 문서 / Reverse-Engineering & Method

전장의 발큐리아 2 (`NPJH50145`, v1.01)를 한국어로 번역하기 위해 게임 데이터 포맷을
역분석하고, 폰트의 한자 자리에 한글을 넣는 **완성형(wansung) 치환 방식**으로 게임 내
텍스트를 한글화한 과정을 정리한 문서입니다. 다른 SJIS 기반 일본 게임의 한글/타언어
패치에도 대부분 그대로 응용됩니다.

> This documents the file-format reverse engineering and the "wansung" (put Hangul into
> the SJIS kanji glyph slots) technique used to Korean-translate VC2 PSP. Most of it
> applies to any SJIS-based Japanese game.

---

## 0. 전체 그림 (Big picture)

```
game.iso  (ISO9660/UMD)
 └─ PSP_GAME/USRDIR/ODIN.CPK        ← 모든 에셋이 든 CRIWARE CPK (4,698 파일)
      ├─ ODIN_FONT_16.BF1           ← 폰트 (SFNT+MFNT). 한자 글리프를 한글로 덮어씀
      ├─ MTPA_*.MTP  (19개)         ← 대사/UI 텍스트 (MTPA 포맷)
      ├─ (DLxx_)GAME_INFO*.MXE      ← 이름/브리핑/사전 (MXE 포맷, 롤링 암호화)
      ├─ MISSION_*.MXE  (191개)     ← 미션 브리핑/전투 대사 (MXE)
      └─ ...
```

패치 파이프라인:
1. **추출** — YACpkTool로 ODIN.CPK를 4,698개 개별 파일로 풀기
2. **복호화·파싱** — 각 파일의 XOR 암호를 풀고 텍스트 위치를 찾기
3. **폰트 제작** — 실제로 쓰는 한글 음절을 렌더링해 BF1의 한자 슬롯에 써넣기
4. **번역·주입** — 일본어 SJIS를 "한자 코드(=한글 글리프)"로 바꿔 넣기, 재암호화
5. **재패킹** — YACpkTool로 CPK 재생성 → UMD-replace로 ISO에 주입
6. **배포** — 원본 ISO와의 xdelta 차분만 배포(저작권 안전)

---

## 1. 도구·환경 (Toolchain)

| 도구 | 용도 | 비고 |
|---|---|---|
| [YACpkTool](https://github.com/Brolijah/YACpkTool) | CPK 추출/재패킹 | ★반드시 실제 콘솔에서 실행(`Start-Process -Wait`). 리다이렉트/헤드리스면 `System.Console.CursorTop` 예외로 조용히 죽음. CpkMaker.dll을 옆에 둘 것. 단일파일 -R/-X는 깨짐 → 전체 추출/재패킹만. |
| UMD-replace (CUE) | ISO 안의 파일 교체 | `UMD-replace <iso> PSP_GAME/USRDIR/ODIN.CPK new.CPK`. LBA/크기 자동 갱신. |
| [pyxdelta](https://pypi.org/project/pyxdelta/) / xdelta3 | 배포용 차분 패치 | `pip install pyxdelta` |
| Python 3 + Pillow | 폰트 렌더링·스크립트 | 한글 TTF 필요(예: 서울한강체) |

> 재패킹은 CRC/그룹 정보를 드롭하지만 게임은 CPK 파일 CRC를 검사하지 않아 무해합니다
> (동일-추출-재패킹 identity 테스트로 확인).

---

## 2. CPK 파일 암호화 (per-file XOR keystream)

각 CPK 내부 파일(=리소스)은 **독립적으로** 다음과 같이 암호화되어 있습니다:

```
key[4] = 첫 16바이트를 uint32 4개로 (리틀엔디안)
offset 16(=0x10)부터 EOF까지, uint32 워드 단위로:
    key[i % 4] = key[i % 4] * 3 + 1        # 워드마다 키 진화
    word[i]   ^= key[i % 4]
```

- **대칭(XOR)** 이므로 같은 루틴이 복호화=암호화. 키스트림은 오직 첫 16바이트에만 의존
  → 본문을 편집하고 **원본 키로 다시 암호화하면 유효한 암호문**이 됩니다.
- 키스트림이 위치에만 의존하므로, 편집한 바이트 위치에서만 암호문이 달라집니다.
- `tools/vc2crypt.py`: `decrypt_resource(raw, 0)`, `encrypt_resource(key16, body)`,
  `find_resources(raw)` (한 파일에 여러 리소스가 있을 수 있음 — MLX 등).

### 평문(plaintext) 스킵의 함정
게임은 헤더가 유효한 "이미 평문인" 파일은 복호화를 건너뜁니다(러시아 패치가 이용한 방식).
그러나 **BF1/MTP를 평문으로 넣으면 부팅 초기/타이틀/동영상 경로가 깨집니다**(글리프는
그려지지만 오프닝 동영상 스킵, 난이도 글자 퍼짐). ⇒ **원본과 동일하게 전부 암호화 상태로
넣는 것이 정답.** (초기 시행착오의 핵심 교훈)

과거 문서(unknownbrackets의 VC3 노트 등)의 "0x800에 메인 리소스, 경계에서 re-key" 설명은
사실 잘못된 파일-오프셋 버그에서 온 착시였습니다. **표준 파일은 `decrypt_resource(raw, 0)`
한 번으로 전체가 깔끔히 복호화**됩니다(단, YACpkTool로 추출한 표준 파일 기준).

---

## 3. 완성형(wansung) 치환 방식

SJIS에는 한글이 없습니다. 대신 **게임 폰트의 한자 글리프 자리에 한글을 그려 넣고**,
대사에는 그 한자의 SJIS 코드를 넣습니다. 게임은 "한자를 렌더"하지만 글리프가 한글이라
화면엔 한글이 나옵니다. ASCII/기호/반각 공백은 그대로 유지됩니다.

- 사용한 매핑: **실제 번역문에 등장한 고유 음절만** 모아 순서대로 한자 슬롯에 배정
  (고정 2350자보다 낫습니다 — 누락 0, 이 패치는 ~1,224자 사용).
- 슬롯: SJIS 리드바이트 `0x88–0x9f`(L1 한자) + `0xe0–0xfc`(L2/확장) = 약 3,000칸.
- 인코더 `tools/wansung_encode.py`: 한글→2바이트 코드, ASCII→1바이트, `\n`→0x0a(또는
  원문이 CRLF면 0x0d0a), 전각 기호(「」…― 등, 리드 0x81/0x84–0x87)는 그대로,
  전각 ASCII→반각 정규화. 폰트에 없는 음절은 예외를 던지므로 누락을 잡을 수 있습니다.

---

## 4. BF1 폰트 포맷

`ODIN_FONT_16.BF1` = SFNT 컨테이너(헤더 0x60) + MFNT 서브리소스들.

- **MFNT#1** @0x60: 반각(1바이트) 96칸 그리드. 슬롯=코드−0x20, 64바이트/글리프, 16행×4바이트,
  **바이트당 MSB-first** 1bpp. (러시아어 등 반각 문자용 — 폭이 좁음)
- **MFNT#2** @0x1880: 전각(한자/한글) 평면. **16×16, 2bpp**(4계조, MSB-first, 4바이트/행,
  0x40바이트/글리프). `pixel(x,y)=(byte[y*4+(x*2)//8]>>(6-(x*2)%8))&3`.
  - 코드→글리프 오프셋: EBOOT `FUN_003c38f4`의 산술을 이식(3개 하위평면).
    `tools/vc2_font2b.py`의 `glyph_offset()`.
  - **전각 advance = de4/de6 = 16/16 = 1.0×fontsize** (완전 정사각 셀). 자동 — HFPR/EBOOT
    수정 불필요. 한글은 전각이므로 일본어 한자와 폭/자간이 자동으로 동일해집니다.
- **HFPR** @0x39ed0: 반각(MFNT#1) 폭 테이블(코드−0x20, 1바이트). 반각 경로에서만 사용.

한글은 전각(2바이트) 경로를 씁니다 — `tools/vc2_hangul_patch.py`가 한글 TTF를 2bpp로
렌더링(정사각 크롭으로 종횡비 보존)해 MFNT#2 슬롯에 써넣습니다.

---

## 5. MTPA 텍스트 포맷 (대사/UI)

```
0x00: "MTPA" | psz | hsz | flags ...
0x20: info_header { u5=0x4000000f, ptr_count, data_size, data_count }
      unknown6[data_size]
      ptr_seg  [u32 × ptr_count]                    (보통 [i*4] 인덱스표)
      data_seg [ (data_size*4) 바이트 × data_count ] 레코드
               dsize=2 → {voiceid, text_pos}        (tpf=1)
               dsize=4 → {flags, voiceid, text_pos, flags3}  (tpf=2)
      text_seg 문자열 풀
```

- **문자열은 파일에서 +1 인코딩**(각 바이트 +1, NUL은 0x01). 게임이 로드시 한 번 −1.
  편집은 −1 도메인에서 하고 쓸 때 +1.
- 각 엔트리 = `[u32 len][payload][NUL 종단+패딩]`, 블록크기 `align_up(4+len+1,4)`.
  `text_pos`는 이 len 헤더를 가리킴.
- **−1 디코드는 로드시 1회 블랭킷 패스**(EBOOT `FUN_003d4dfc`). 그 범위 밖에 append하면
  −1이 안 걸려 깨짐(공백→'!', 개행 안 됨). ⇒ **반드시 원래 텍스트 영역 안에서 in-place 편집.**
- `tools/mtpa_edit.py`의 `rebuild_inplace(body, {rec: payload})` = 안전한 주입:
  각 레코드 엔트리를 원래 할당 블록 안에서 덮어씀(새 payload ≤ 원래). text_pos/다른
  레코드/트레일링 패킷(ENRS/EOFC)/packet_size를 바이트 단위로 보존.

---

## 6. MXE 포맷 (이름·브리핑·사전) — ★가장 까다로웠던 부분

`(DLxx_)?GAME_INFO*.MXE`, `MISSION_*.MXE`. 구조:

```
MXEN 컨테이너 헤더
 └─ MXEC 패킷: [magic|psz|hsz|flags(+0xc)|...|datasize(+0x14)|...]
      [DATA  = datasize 바이트]   ← something1 레코드 + 데이터블록 + 문자열 풀
      [POF0] 포인터 재배치 테이블   ← 로드시 포인터에 베이스주소를 더함
      [ENRS] 엔디안 재배치
      [CCRS] ...
```

- **MXEC flags 비트 `0x40000`이 서면 DATA가 롤링 XOR로 암호화**되어 있습니다
  (`plain[i] = enc[i] ^ enc[i-1]`, 첫 바이트는 그대로). vc3_formats 문서 참조.
- something1 레코드 = `{u32 id, u32 type_ptr(→ASCII 타입명), u32 length, u32 data_ptr}`.
  포인터 절대오프셋 = `0x20 + 값`. 표시 문자열은 데이터블록 뒤 **문자열 풀**에 있고
  타입명("VlMxMissionDetailedInfo" 등)은 ASCII라 한글 편집 대상이 아닙니다.

### ★★ 결정적 버그 — 롤 영역을 datasize까지만 잡을 것
롤 암호화 영역은 **오직 DATA `[start, start+datasize)`** 이며 뒤의 POF0/ENRS/CCRS는
**암호화되지 않습니다**(게임은 그 부분을 롤-복호화하지 않고 그대로 읽음).

처음엔 롤 영역을 **패킷 전체(psz)** 로 잡았는데, 그러면 문자열을 하나만 바꿔도
**재암호화의 체인 전파(enc[i]=plain[i]^enc[i-1])가 POF0/ENRS 바이트까지 변조**합니다.
게임이 손상된 재배치 테이블로 포인터를 재배치하다 **쓰레기 주소로 점프/쓰기 → 크래시**
(GAME_INFO는 부팅 시, MISSION은 전투/브리핑 로드 시). 이 때문에 한동안 "GAME_INFO엔
부팅 무결성 검사가 있다"고 오판했지만, **사실은 이 롤-영역 버그 하나가 모든 MXE 크래시의
원인**이었습니다.

수정: `tools/mxe_tool.py`의 `body_range()`에서 `end = start + u32@(MXEC+0x14)`(=POF0 직전).
검증: 편집 후 POF0/ENRS 영역이 원본과 바이트 단위로 동일, identity 라운드트립 통과.
⇒ 동일-길이 문자열 편집이면 재배치 테이블이 온전 → 안전. GAME_INFO도 부팅 정상.

---

## 7. 중첩(nested) MTP 처리

일부 이벤트 파일(EV30xxx, EV50001, SLG_EV)은 표준 MTPA가 아니라 **컨테이너**로,
`text_pos`가 `[len][text]`를 일관되게 가리키지 않고 텍스트가 흩어져 있습니다
(레코드 영역 뒤에 텍스트 블록이 섞임). `rebuild_inplace`로는 위험.

대신 `tools/nested_runs.py`처럼 **−1 도메인 바디에서 전각 SJIS 런을 찾아 동일 길이로 치환**
(부족분은 공백 패딩)합니다. 마커(`02 00 00 00` 등)·길이 필드·NUL은 전각 SJIS 리드가
아니므로 런에 포함되지 않아 구조가 보존됩니다.

**안전 검증(중요):** 편집 후 실제 데이터 레코드의 `text_pos`가 하나도 바뀌지 않았는지
확인하세요. (표준 파싱은 dcount만큼 레코드를 읽지만 대부분 텍스트를 레코드로 오파싱합니다
— 원래 `text_pos`가 유효했던 레코드만 "진짜"로 보고, 그 값들이 불변이면 안전.)

---

## 8. 파이프라인 상세 (재현 방법)

1. **추출**: `YACpkTool ODIN.CPK ODIN_out/` → 4,698 파일.
2. **텍스트 추출**: 각 MTP는 `mtpa_edit`로, 각 MXE는 `mxe_tool.decrypt_file`+`extract_runs`로
   일본어 SJIS를 뽑음. (금지어 필터 등 비표시 데이터는 제외 — §9)
3. **번역**: JP→KO. 각 문장이 원래 바이트 예산에 맞아야 함(한글=2B, ASCII=1B).
4. **폰트**: 번역에 쓰인 고유 음절을 모아 `wansung_encode.build_mapping`/`build_font`로
   BF1의 한자 슬롯에 렌더링.
5. **주입**:
   - clean MTP → `mtpa_edit.rebuild_inplace`
   - nested MTP → `nested_runs` 동일 길이 런 치환
   - MXE → `mxe_tool`(고친 롤 영역) 동일 길이 문자열 치환 후 롤+파일 재암호화
6. **재패킹**: 편집 파일을 추출폴더에 덮고 `YACpkTool ODIN_out/ ODIN2.CPK`.
7. **주입**: `UMD-replace game.iso PSP_GAME/USRDIR/ODIN.CPK ODIN2.CPK`.
8. **작은 배포 패치**: 편집 파일은 전부 원본과 **동일 크기**이므로, 재패킹 대신
   **원본 CPK를 in-place로 덮어써** ISO 변경분을 최소화(≈2.5MB)한 뒤 xdelta를 뜨면
   패치가 ~0.8MB로 작아집니다(재패킹은 전체 레이아웃을 흔들어 xdelta가 258MB로 커짐).

---

## 9. 함정·교훈 (Gotchas)

- **금지어 필터**: `MTPA_GAME` 뒤쪽 레코드(~1937–2941)는 화면에 안 나오는 **비속어/차별어
  입력 필터 목록**입니다. 번역하면 (1)부적절 문자열을 찍고 (2)필터가 무력화됩니다 →
  **원문 유지.**
- **엔진 내부 이름**: `GAME_INFO_MAP_OBJECT`의 `ユニット配置場所`, `気象・吹雪` 등은 표시용이
  아니라 엔진 참조 식별자 → 번역 금지(러시아 패치도 원문 유지). RUS가 손댄 파일 목록을
  화이트리스트로 쓰면 안전.
- **CRLF vs LF**: 개행을 원문과 동일(대부분 LF, 오프닝 나레이션 일부는 CRLF)하게 보존.
- **부팅 vs 전투 로드**: GAME_INFO는 부팅 시 로드되어 자동 부팅 테스트로 검증 가능하지만,
  MISSION/nested/SLG_EV는 **전투 로드 시** 로드되어 부팅 테스트로 못 잡습니다 → 실기/에뮬
  전투 진입 확인이 필요.
- **부팅 테스트 하네스**: `tools/boottest.py` — PPSSPP로 ISO 실행 후 에뮬 RAM의 복호화
  매직 개수를 세어(≈845=메뉴 진입, ≈256–430=크래시) 부팅 성패를 자동 판정.

---

## 10. 남은 것 (Not done)

- **텍스처(HTX/MLX)에 구워진 글자**(전적 화면 헤더·HUD 라벨) — 이미지 재드로잉 필요.
- **동영상(PMF) 자막** — 하드섭 재인코딩 필요.
- MXE 편집이 가능해졌으므로 이론상 EBOOT 수정 없이 텍스트는 거의 100% 가능합니다.

## 참고

- unknownbrackets, VC3 파일 포맷 노트(gist) — CPK/MTPA/MXE의 초기 단서.
- VC2 러시아어 팬패치(team MOSAS) — 편집 대상 파일 화이트리스트의 기준.
