import os
import pytest
import time
import logging

from main import search

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@pytest.mark.parametrize(
    "query_video, actual",
    [
        ("../needles/needle1.mp4", 16200),
        ("../needles/needle2.mp4", 8340),
        ("../needles/needle3.mp4", 13350),
        ("../needles/needle4.mp4", 8880),
        ("../needles/needle5.mp4", 14310),
        ("../needles/needle6.mp4", 12240),
        ("../needles/needle7.mp4", 870),
        ("../needles/needle8.mp4", 15750),
        ("../needles/needle9.mp4", 5250),
        ("../needles/needle10.mp4", 30),
    ],
)
def test_video_match(query_video, actual):
    start_time = time.time()

    try:
        # Run the main function with the query video
        discovered = search(query_video)

        # Check if the test case took more than a minute
        elapsed_time = time.time() - start_time
        if elapsed_time > 60:
            logging.error(
                f"Test case for {query_video} took more than a minute. Execution time: {elapsed_time:.2f} seconds"
            )
            assert (
                False
            ), f"Test case for {query_video} exceeded the time limit of 1 minute"

        # Calculate the frame offset
        frame_offset = abs(discovered - actual)

        # Check the frame offset and log appropriate messages
        if frame_offset >= 5:
            logging.error(
                f"Test case for {query_video} failed. Frame offset: {frame_offset}"
            )
            assert (
                False
            ), f"Frame offset of {frame_offset} exceeds the maximum allowed offset of 5 frames"
        elif frame_offset >= 2:
            logging.warning(
                f"Test case for {query_video} passed with a warning. Frame offset: {frame_offset}"
            )
            assert (
                True
            ), f"Frame offset of {frame_offset} is within the warning threshold of 2 frames"
        else:
            logging.info(
                f"Test case for {query_video} passed. Execution time: {elapsed_time:.2f} seconds"
            )
            assert True
    except Exception as e:
        logging.error(f"Test case for {query_video} failed. Error: {str(e)}")
        raise


if __name__ == "__main__":
    pytest.main(["-v", __file__])
