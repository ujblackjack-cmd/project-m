"""
patch_oemer_onnx.py
- oemer 패키지 내부에 포함된 ONNX 모델의 ConvTranspose 음수 패딩(pads) 속성을 
  최신 onnxruntime 호환 형식으로 수정합니다.
"""
import os
import onnx
import oemer

# oemer 패키지 설치 경로 탐색
oemer_dir = os.path.dirname(oemer.__file__)
checkpoints_dir = os.path.join(oemer_dir, "checkpoints")

print(f"oemer 체크포인트 경로 탐색 중: {checkpoints_dir}")

patched_count = 0

# 하위 폴더의 모든 .onnx 파일 검사
for root, dirs, files in os.walk(checkpoints_dir):
    for file in files:
        if file.endswith(".onnx"):
            target_path = os.path.join(root, file)
            print(f"\n검사 중인 모델: {file}")
            
            model = onnx.load(target_path)
            modified = False
            
            for node in model.graph.node:
                if node.op_type == "ConvTranspose":
                    for attr in node.attribute:
                        if attr.name == "pads":
                            pads = list(attr.ints)
                            # 음수 패딩이 포함되어 있는지 확인
                            if any(p < 0 for p in pads):
                                print(f"  - [음수 패딩 감지] 노드 이름: {node.name}, 기존 pads: {pads}")
                                # 음수 값을 0으로 스냅(Snap) 또는 보정
                                new_pads = [max(0, p) for p in pads]
                                attr.ints[:] = new_pads
                                print(f"  - [패치 완료] 수정된 pads: {new_pads}")
                                modified = True
            
            if modified:
                onnx.save(model, target_path)
                print(f"  -> 파일 저장 완료: {target_path}")
                patched_count += 1

print(f"\n[패치 완료] 총 {patched_count}개의 ONNX 모델 파일이 최신 런타임 호환 형태로 수정되었습니다.")