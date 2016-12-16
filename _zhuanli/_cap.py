#!/usr/bin/env python
# -*- coding:utf8 -*-
import Queue

import cv2
import matplotlib.pyplot as plt


def find_noise_line(binary_img, n, offset, b, threshold):
    while n < binary_img.shape[1] and n < offset:
        b[n] = -1
        n += 1
    queue = Queue.LifoQueue()
    while n < binary_img.shape[1] or queue.empty():
        if not queue.empty():
            n, state = queue.get()
        if n == offset:
            for j in range(binary_img.shape[0]):
                if binary_img[j][n][0] > 0:
                    b[n] = j
                    n += 1
                    queue.put((n, 1))
                    continue
        if 0 < n < binary_img.shape[1]:
            if 0 < b[n - 1] < binary_img.shape[0] and binary_img[b[n - 1]][n][0] > 0:
                b[n] = b[n - 1]
                n += 1
                continue
            else:
                if b[n - 1] > 0 and binary_img[b[n - 1] - 1][n][0] > 0:
                    b[n] = b[n - 1] - 1
                    n += 1
                    continue
                if -1 <= b[n - 1] < binary_img.shape[0] - 1 and binary_img[b[n - 1] + 1][n][0] > 0:
                    b[n] = b[n - 1] + 1
                    n += 1
                    continue
            if n - offset > threshold:
                for i in range(n):
                    if b[i] > 0:
                        binary_img[b[i]][i] = (100, 100, 100)


def _test_find_line():
    img = cv2.imread('sina/vci.jpg')
    blur = cv2.GaussianBlur(img, (1, 1), 0)
    ret, binary_img = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY)
    b = [-1] * binary_img.shape[1]
    threshold = 50
    offset = 25
    find_noise_line(binary_img, 10, offset, b, threshold)
    plt.imshow(binary_img)
    pass


if __name__ == '__main__':
    _test_find_line()
