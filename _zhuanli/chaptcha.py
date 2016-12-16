#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy

import cv2
import matplotlib.pyplot as plt


class NoiseLine():
    def __init__(self):
        self.img = None
        self.b = []
        self.threshold = 100
        self.offset = 20
        self.origin = None

    def load(self, imgfile):
        self.origin = cv2.imread(imgfile)
        self.img = copy.deepcopy(self.origin)

    def blur(self, m, s):
        blur = cv2.GaussianBlur(self.origin, (m, s), 0)
        ret, binary_img = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY)
        self.img = binary_img
        self.b = [-1] * binary_img.shape[1]

    def run(self, imf):
        self.load(imf)
        self.show()
        count = 1
        while count > 0:
            self.find_line(0)
            self.b = [-1] * self.img.shape[1]
            count -= 1
        self.show()
        self.save()

    def find_line(self, n):
        while n < self.offset:
            self.b[n] = -1
            n += 1
        if n == self.offset:
            for j in range(self.img.shape[0]):
                if self.img[j][n][2] == 0:
                    self.b[n] = j
                    self.find_line(n + 1)
        if 0 < n < self.img.shape[1]:
            has_more = False
            if self.img.shape[0] > self.b[n - 1] > 0 == self.img[self.b[n - 1]][n][2]:
                self.b[n] = self.b[n - 1]
                has_more = True
                self.find_line(n + 1)
            else:
                if self.b[n - 1] > 0 and self.img[self.b[n - 1] - 1][n][2] == 0:
                    self.b[n] = self.b[n - 1] - 1
                    has_more = True
                    self.find_line(n + 1)
                if self.b[n - 1] < self.img.shape[0] - 1 and self.img[self.b[n - 1] + 1][n][2] == 0:
                    self.b[n] = self.b[n - 1] + 1
                    has_more = True
                    self.find_line(n + 1)
            if n - self.offset > self.threshold and not has_more:
                for i in range(n):
                    if self.b[i] > 0:
                        self.img[self.b[i]][i] = (255, 255, 255)

    def show(self):
        if self.img is not None:
            plt.imshow(self.img)

    def save(self):
        if self.img is not None:
            cv2.imwrite('result.jpg', self.img)


def image_blur_test(imgfile):
    fl = NoiseLine()
    fl.load(imgfile)
    for i in range(1, 21, 2):
        for j in range(1, 21, 2):
            fl.blur(i, j)
            fl.find_line(0)
            cv2.imwrite('blur_%d_%d.jpg' % (i, j), fl.img)


def _test_find_line(img):
    # img = cv2.imread('sina/vci.jpg')
    # blur = cv2.GaussianBlur(img, (1, 1), 0)
    # ret, binary_img = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY)
    # b = [-1] * binary_img.shape[1]
    # threshold = 50
    # offset = 25
    # find_noise_line(binary_img, 10, offset, b, threshold)
    # plt.imshow(binary_img)
    # pass
    fl = NoiseLine()
    fl.load(img)
    fl.blur(3, 3)
    fl.threshold = 150
    fl.offset = 20
    fl.find_line(0)
    cv2.imwrite('result0.jpg', fl.img)
    # fl.threshold = 100
    # fl.offset = 45
    # fl.find_line(0)
    # cv2.imwrite('result1.jpg', fl.img)
    img = cv2.GaussianBlur(fl.img, (7, 9), 0)
    cv2.imwrite('result2.jpg', img)
    binary = fl.img[10:-2, 40:-36]
    cv2.imwrite('bin.jpg', binary)
    outfile = '%d.png'
    for i in range(5):
        single = binary[0:, 25 * i:25 * i + 25]
        cv2.imwrite(outfile % i, single)
    pass


if __name__ == '__main__':
    # image_blur_test('sina/vci/p4g3e.png')
    _test_find_line('sina/vci/p4g3e.png')
