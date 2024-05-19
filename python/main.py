import cv2
import sys
import imagehash
from PIL import Image
import os
import multiprocessing
from multiprocessing import freeze_support

CR = " " * 20 + "\r"
haystack_dir = "../haystacks"
hash_threshold = 10
skip_clip_keyframe_1 = 37
skip_clip_keyframe_2 = 31
skip_clip_keyframe_3 = 1
num_processes = 8


def compute_hash(image):
    return imagehash.dhash(Image.fromarray(image))


def extract_keyframes(video_path, interval):
    """
    Extract keyframes from a video at the specified interval.
    """
    print(f"Extracting keyframes from video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    keyframes = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) % interval == 0:
            print(f"Extracted {int(cap.get(cv2.CAP_PROP_POS_FRAMES))} frames.", end=CR)
            keyframes.append((int(cap.get(cv2.CAP_PROP_POS_FRAMES)), frame))
    cap.release()
    return keyframes


def process_video_chunk(chunk_info):
    """
    Process a chunk of a video to find similar frames.
    """
    video_path, start_frame, end_frame, needle_hashes, hash_threshold = chunk_info
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frame_count = start_frame
    similar_frames = []
    while frame_count <= end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += skip_clip_keyframe_3
        hash = compute_hash(frame)
        for needle_hash in needle_hashes:
            hamming_distance = imagehash.hex_to_hash(
                str(needle_hash)
            ) - imagehash.hex_to_hash(str(hash))
            if hamming_distance <= hash_threshold:
                similar_frames.append((frame_count, hash, hamming_distance))
                break
    cap.release()
    return similar_frames


def process_video_parallel(video_path, needle_hashes, hash_threshold, num_processes):
    """
    Process a video in parallel to find similar frames.
    """
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    chunk_size = frame_count // num_processes
    chunks = [
        (
            video_path,
            i * chunk_size,
            (i + 1) * chunk_size - 1 if i < num_processes - 1 else frame_count - 1,
            needle_hashes,
            hash_threshold,
        )
        for i in range(num_processes)
    ]

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.map(process_video_chunk, chunks)

    similar_frames = [frame for chunk_results in results for frame in chunk_results]
    return similar_frames


class KeypointAttributes:
    """
    A class to store keypoint attributes.
    """

    def __init__(self, keypoint):
        self.pt = keypoint.pt
        self.size = keypoint.size
        self.angle = keypoint.angle
        self.response = keypoint.response
        self.octave = keypoint.octave
        self.class_id = keypoint.class_id


def compute_sift_features(image):
    """
    Compute SIFT features for an image.
    """
    sift = cv2.SIFT_create()
    keypoints, descriptors = sift.detectAndCompute(image, None)
    keypoint_attrs = [KeypointAttributes(kp) for kp in keypoints]
    return keypoint_attrs, descriptors


def match_sift_features(descriptors1, descriptors2):
    """
    Match SIFT features between two sets of descriptors.
    """
    if (
        descriptors1 is None
        or descriptors2 is None
        or len(descriptors1) == 0
        or len(descriptors2) == 0
    ):
        return []

    flann_params = dict(algorithm=1, trees=5)
    flann = cv2.FlannBasedMatcher(flann_params, {})

    k = min(2, len(descriptors1), len(descriptors2))
    matches = flann.knnMatch(descriptors1, descriptors2, k=k)

    good_matches = []
    if k == 1:
        good_matches = matches
    else:
        for m, n in matches:
            if m.distance < 0.9 * n.distance:
                good_matches.append(m)

    return good_matches


def match_keyframes(args):
    """
    Match keyframes between a clip and a reference video.
    """
    i, clip_kp_attrs, clip_desc, reference_features = args
    max_matches = 0
    best_match = None
    for j, (ref_kp_attrs, ref_desc) in enumerate(reference_features):
        if clip_desc is not None and ref_desc is not None:
            feature_matches = match_sift_features(clip_desc, ref_desc)
            if len(feature_matches) > max_matches:
                max_matches = len(feature_matches)
                best_match = (i, j)
    return best_match, max_matches


def find_best_match(clip_path, reference_path, num_processes):
    """
    Find the best match between a clip and a reference video.
    """
    clip_keyframes = extract_keyframes(clip_path, interval=skip_clip_keyframe_1)
    reference_keyframes = extract_keyframes(
        reference_path, interval=skip_clip_keyframe_2
    )

    clip_features = [compute_sift_features(frame) for _, frame in clip_keyframes]
    print("Extracted SIFT features for clip keyframes.")
    reference_features = [
        compute_sift_features(frame) for _, frame in reference_keyframes
    ]
    print("Extracted SIFT features for reference keyframes.")

    print(
        f"Clip frames: {len(clip_features)}, Reference frames: {len(reference_features)}"
    )

    args_list = [
        (i, clip_kp_attrs, clip_desc, reference_features)
        for i, (clip_kp_attrs, clip_desc) in enumerate(clip_features)
    ]

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.map(match_keyframes, args_list)

    best_match_index, _ = max(results, key=lambda x: x[1])

    if best_match_index is not None:
        clip_frame_index = clip_keyframes[best_match_index[0]][0]
        reference_frame_index = reference_keyframes[best_match_index[1]][0]
        return clip_frame_index, reference_frame_index
    else:
        return None


def search(video_path):
    freeze_support()

    needle_video = video_path
    files = sorted(
        os.listdir(haystack_dir),
        key=lambda x: int(x.split(".")[0].replace("haystack", "")),
    )
    print(f"Found {len(files)} files.")
    needle_keyframes = extract_keyframes(needle_video, interval=skip_clip_keyframe_1)
    needle_hashes = [compute_hash(frame) for _, frame in needle_keyframes]

    print(f"Extracted {len(needle_keyframes)} keyframes from the needle video.")

    best_video = None
    max_similar_frames = 0

    for haystack_video in files:
        if haystack_video.endswith(".mp4"):
            haystack_video_path = os.path.join(haystack_dir, haystack_video)
            similar_frames = process_video_parallel(
                haystack_video_path, needle_hashes, hash_threshold, num_processes
            )
            if similar_frames:
                if len(similar_frames) > max_similar_frames:
                    max_similar_frames = len(similar_frames)
                    best_video = haystack_video
                print(
                    f"Found {len(similar_frames)} similar frames in {haystack_video}."
                )
            else:
                print(f"No similar frames found in {haystack_video}", end=CR)

    if best_video:
        print(f"Best video: {best_video}, Similar frames: {max_similar_frames}")
        best_match_index = find_best_match(
            needle_video, os.path.join(haystack_dir, best_video), num_processes
        )
        if best_match_index is not None:
            clip_frame_index, reference_frame_index = best_match_index
            print(f"Best match found:")
            print(f"Clip frame index: {clip_frame_index}")
            print(f"Reference video frame index: {reference_frame_index}")
            os.system(
                f"mpv --start={reference_frame_index-clip_frame_index} {os.path.join(haystack_dir, best_video)}"
            )
            return reference_frame_index
        else:
            print("No match found.")
    else:
        print("No matching video found.")


if __name__ == "__main__":
    search(sys.argv[1])
