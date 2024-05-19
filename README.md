# Video Search
This project searches and indexes into videos (with audio) and finds the matching video for any given video snippet between 20 and 40 seconds. The query video snippet is processed to create a digital signature, which is then compared with the digital signatures of the videos in the database to find the best match. The clip is then played starting from the matched frame via the VLC media player.  

Some of the key features of the project are:
1. **Video Indexing**: The project indexes the videos in the database by extracting video features via image hashing and Scale-invariant feature transform (SIFT).
2. **Signature Matching**: The project matches the query video snippet with the videos in the database using the Hamming distance to measure the similarity between the digital signatures and identify the source video.
3. **Start Frame Identification**: Keyframes are extracted from the video at regular intervals, and the best matching start frame is identified by comparing SIFT features of the keyframes.
4. **Parallel Processing**: The project uses parallel processing to speed up the indexing and matching process by dividing each video into chunks, each of which is processed by a separate thread.
5. **Output Visualization**: The project visualizes the output by playing the matched video starting from the matched frame via the VLC media player.
 
### Running the project
1. Clone the repository.
2. For Windows, open the project in Visual Studio and run the `VideoSearch.sln` file. The project will be called as follows: `VideoSearch.exe <QueryVideo.mp4> <QueryAudio.wav>`. For Mac, run the Python file `main/test_search.py` which runs several tests automatically. These tests can be modified to test different videos contained in the `haystacks` folder to find a given video snippet contained in the `needles` folder.