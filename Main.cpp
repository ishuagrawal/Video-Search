#include <opencv2/core.hpp>
#include <opencv2/videoio.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/highgui.hpp>
#include <iostream>
#include "img_hash.hpp"

#include <string>
#include <fstream>
#include <map>
#include <opencv2/imgproc.hpp>
#include <opencv2/imgproc/types_c.h>
#include <Windows.h>

typedef std::map<int, std::vector<uint64_t>> Database;

using namespace cv;

Database haystacks;

std::string haystack_dir = "haystacks";
int hash_threshold = 8;
int skip_clip_keyframe_1 = 3;
int skip_clip_keyframe_2 = 31;
int skip_clip_keyframe_3 = 1;
int num_processes = 8;

int computeHammingDist(uint64_t& a, uint64_t& b)
{
    uint64_t x = a ^ b;
    int setBits = 0;

    while (x > 0) {
        setBits += x & 1;
        x >>= 1; 
    }

    return setBits;
}

void extractKeyHashes(std::string& path, int interval, std::vector<std::pair<int, uint64_t>>& keyframes)
{
    VideoCapture inputVid = VideoCapture(path);

    Mat nextFrame;
    std::vector<uchar> hashVec;
    uchar hashChars[8];
    uint64_t hash;
    while (true)
    {
        int currframe = int(inputVid.get(CAP_PROP_POS_FRAMES));
        inputVid >> nextFrame;
        if (nextFrame.empty())
            break;

        if (currframe % interval == 0)
        {
            cv::img_hash::pHash(nextFrame, hashVec);
            for (int i = 0; i < 8; i++)
                hashChars[i] = hashVec[i];

            memcpy(&hash, hashChars, sizeof(hash));

            keyframes.push_back(std::make_pair(currframe / interval, hash));
        }
    }
    inputVid.release();
}

int playVideoDebug(int startframe, std::string hayVideo, std::string needleVideo)
{
    float startTime = (float)startframe / 30.0f;
    std::string start = "C:\\Users\\louis\\CSCI576\\FinalProject\\VideoSearch\\";
    std::string command = "c:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe --play-and-exit --start-time=" + std::to_string(startTime) + " " + start + hayVideo;
    
    const char* commandChars = command.c_str();

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    memset(&si, 0, sizeof(si));
    si.cb = sizeof(si);
    memset(&pi, 0, sizeof(pi));

    char buf[MAX_PATH + 300];
    wsprintfA(buf, "%s", commandChars);
    CreateProcessA(0, buf, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi);

    return 0;
}

void search(std::string inputVideoPath, int skipInterval)
{
    std::cout << "searching " << inputVideoPath << "...\n";
    //frame hash pairs
    std::vector<std::pair<int, uint64_t>> needleKeyframes;

    extractKeyHashes(inputVideoPath, skipInterval, needleKeyframes);
    int minVidDist = INT_MAX, vid = -1, vidInd = -1;
    for (int haystack = 1; haystack <= 20; haystack++)
    {
        int hits = 0;
        int minDist = INT_MAX, ind = -1;
        int haystackSize = haystacks[haystack].size();
        for (int hayHash = 0; hayHash < haystackSize; hayHash++)
        {
            if (hayHash + skipInterval * (needleKeyframes.size() - 1) > haystackSize)
                break;

            int hammingSum = 0;
            for (int needleFrame = 0; needleFrame < needleKeyframes.size(); needleFrame++)
            {
                int hammingDist = computeHammingDist(haystacks[haystack][hayHash + needleFrame * skipInterval], needleKeyframes[needleFrame].second);
                hammingSum += hammingDist;
            }
            if (hammingSum < minDist) {
                minDist = hammingSum;
                ind = hayHash;
            }

            if (hammingSum < hash_threshold * needleKeyframes.size())
                hits++;

        }
        if (minDist < minVidDist) {
            minVidDist = minDist;
            vid = haystack;
            vidInd = ind;
        }
    }
    std::cout << "\tFOUND video " << vid << " @ frame " << vidInd << ", min hamming dist=" << minVidDist << std::endl;
    playVideoDebug(vidInd, "haystacks\\haystack" + std::to_string(vid) + ".mp4", inputVideoPath);

}

void hashHaystack(std::string intputFile, std::string outputFile)
{
    std::ofstream haystackOuput;
    haystackOuput.open(outputFile, std::ios::binary);

    int frames = 0;
    VideoCapture inputVid = VideoCapture(intputFile);
    Mat nextFrame, resizedFrame;
    while (true)
    {
        inputVid >> nextFrame;

        if (nextFrame.empty())
            break;
        frames++;

        cv::resize(nextFrame, resizedFrame, cv::Size(nextFrame.cols * 0.5, nextFrame.rows * 0.5), 0, 0, CV_INTER_LINEAR);
        std::vector<uchar> hash;

        cv::img_hash::pHash(resizedFrame, hash);
        for (int j = 0; j < 8; j++)
            haystackOuput << hash[j];
    }
    std::cout << frames << "\n";
    inputVid.release();

    haystackOuput.close();
}

void createDatabase()
{
    for (int i = 1; i <= 20; i++)
    {
        std::string input = "haystacks/haystack" + std::to_string(i) + ".mp4";
        std::string output = "hashedHaystacks/hashHaystack" + std::to_string(i) + ".hay";
        hashHaystack(input, output);
    }
}

int main(int argc, char* argv[])
{
    //createDatabase();
    //Setup the Database
    for (int i = 1; i <= 20; i++)
    {
        std::ifstream iFile("hashedHaystacks/hashHaystack" + std::to_string(i) + ".hay", std::ios::in | std::ios::binary | std::ios::ate);
        std::streampos filesize = iFile.tellg();

        iFile.seekg(0, std::ios::beg);
        char* memblock = new char[filesize];
        iFile.read(memblock, filesize);
        iFile.close();

        uint64_t hash;
        int pos = 0;
        uchar hashChars[8];
        std::vector<uint64_t> hashVals;
        while (pos + 8 < filesize)
        {
            for (int p = 0; p < 8; p++)
                hashChars[p] = memblock[pos++];

            memcpy(&hash, hashChars, sizeof(hash));
            hashVals.push_back(hash);
        }
        haystacks[i] = hashVals;
        iFile.close();
        delete[] memblock;
    }

    for (int i = 7; i <= 7; i++) {
        search(std::string(argv[1]), skip_clip_keyframe_1);
    }
}