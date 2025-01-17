import numpy as np
import skimage.transform as skiT

from . import Stimulus


class barStimulus(Stimulus):
    """Define a Stimulus of eight bars crossing though the FoV from different dicetions"""

    def __init__(
        self,
        stimSize=101,
        maxEcc=7,
        overlap=1 / 2,
        nBars=1,
        doubleBarRot=0,
        thickRatio=1,
        continous=False,
        TR=2,
        stim_duration=336,
        blank_duration=12,
        loadImages=None,
        flickerFrequency=8,
        forceBarWidth=None,
        continous_multiplier=2,
        startingDirection=[0, 3, 6, 1, 4, 7, 2, 5],
    ):
        super().__init__(
            stimSize,
            maxEcc,
            TR=TR,
            stim_duration=stim_duration,
            blank_duration=blank_duration,
            loadImages=loadImages,
            flickerFrequency=flickerFrequency,
            continous=continous,
        )
        self.stimulus_type = "bar"

        self.startingDirection = startingDirection

        self.nBars = nBars
        self.doubleBarRot = doubleBarRot
        self.thickRatio = thickRatio

        self.forceBarWidth = forceBarWidth

        self.crossings = len(self.startingDirection)
        self.nBlanks = 4

        self.framesPerCrossing = int(
            (self.nFrames - self.nBlanks * self.blankLength) / self.crossings
        )

        if self.forceBarWidth is not None:
            forceBarWidthPix = np.ceil(
                self.forceBarWidth / (2 * self._maxEcc) * self._stimSize
            ).astype("int")
            self.bar_width = forceBarWidthPix
            self.overlap = (self._stimSize + 0.5) / (
                self.bar_width * self.framesPerCrossing
            )
        else:
            self.overlap = overlap
            self.bar_width = np.ceil(
                self._stimSize / (self.framesPerCrossing * self.overlap - 0.5)
            ).astype("int")

        if not continous:
            self.continous = False
            self._stimRaw = np.zeros((self.nFrames, self._stimSize, self._stimSize))
            self._stimBase = np.zeros(self.nFrames)  # to find which checkerboard to use

            self.jump_size = self.overlap * self.bar_width

            it = 0
            for cross in self.startingDirection:
                for i in range(self.framesPerCrossing):
                    frame = np.zeros((self._stimSize, self._stimSize))
                    frame[
                        :,
                        max(0, int(self.jump_size * (i - 1))) : min(
                            self._stimSize,
                            int(self.jump_size * (i - 1) + self.bar_width),
                        ),
                    ] = 1

                    if self.nBars > 1:
                        self.nBarShift = self._stimSize // self.nBars
                        frame2 = np.zeros((self._stimSize, self._stimSize))
                        frame3 = np.zeros((self._stimSize, self._stimSize))

                        for nbar in range(self.nBars - 1):
                            if i == 0:
                                o = max(
                                    int(np.ceil(self._stimSize / 2 - 1)),
                                    int(
                                        self.jump_size * (i - 1)
                                        + self.bar_width * self.thickRatio * 0.55
                                        + self.nBarShift * (nbar + 1)
                                    ),
                                )
                                t = int(
                                    self.jump_size * (i - 1)
                                    + self.bar_width * self.thickRatio
                                    + self.nBarShift * (nbar + 1)
                                )
                            elif i == self.framesPerCrossing - 1:
                                o = int(
                                    self.jump_size * (i - 1)
                                    + self.nBarShift * (nbar + 1)
                                )
                                t = int(
                                    self.jump_size * (i - 1)
                                    + self.bar_width * self.thickRatio * 0.45
                                    + self.nBarShift * (nbar + 1)
                                )
                            else:
                                o = int(
                                    self.jump_size * (i - 1)
                                    + self.nBarShift * (nbar + 1)
                                )
                                t = int(
                                    self.jump_size * (i - 1)
                                    + self.bar_width * self.thickRatio
                                    + self.nBarShift * (nbar + 1)
                                )

                            frame2[:, max(0, o) : min(self._stimSize, t)] = 1
                            frame3[
                                :,
                                max(0, o - self._stimSize) : max(
                                    0,
                                    min(
                                        int(np.floor(self._stimSize / 2)),
                                        min(self._stimSize, t - self._stimSize),
                                    ),
                                ),
                            ] = 1

                            frame2 = skiT.rotate(frame2, self.doubleBarRot, order=0)
                            frame3 = skiT.rotate(frame3, self.doubleBarRot, order=0)
                            frame = np.any(np.stack((frame, frame2, frame3), 2), 2)

                    self._stimRaw[it, ...] = skiT.rotate(
                        frame, cross * 360 / self.crossings, order=0
                    )

                    self._stimBase[it] = np.mod(cross, 2) + 1

                    it += 1

                if cross % 2 != 0:
                    it += self.blankLength

            self._create_mask(self._stimRaw.shape)

            self._stimUnc = np.zeros(self._stimRaw.shape)
            self._stimUnc[:, self._stimMask] = self._stimRaw[:, self._stimMask]

        else:
            self.continous = True
            self.frameMultiplier = self.TR * continous_multiplier
            self.nContinousFrames = int(self.nFrames * self.frameMultiplier)
            self.continousBlankLength = int(blank_duration * self.frameMultiplier)
            self.framesPerCrossing = int(
                (self.nContinousFrames - 4 * self.continousBlankLength) / self.crossings
            )

            self._stimRaw = np.zeros(
                (self.nContinousFrames, self._stimSize, self._stimSize)
            )
            self._stimBase = np.zeros(
                self.nContinousFrames
            )  # to find which checkerboard to use

            self.jump_size = self.overlap * self.bar_width / self.frameMultiplier

            it = 0
            for cross in self.startingDirection:
                for i in range(self.framesPerCrossing):
                    frame = np.zeros((self._stimSize, self._stimSize))
                    frame[
                        :,
                        max(
                            0,
                            int(self.jump_size * (i - self.frameMultiplier)),
                        ) : min(
                            self._stimSize,
                            int(
                                self.jump_size * (i - self.frameMultiplier)
                                + self.bar_width
                            ),
                        ),
                    ] = 1

                    # if self.nBars > 1:
                    #     self.nBarShift = self._stimSize // self.nBars
                    #     frame2 = np.zeros((self._stimSize,self._stimSize))

                    #     for nbar in range(self.nBars-1) :
                    #         o = int(self.overlap*self.bar_width*(i-1) + self.nBarShift*(nbar+1))
                    #         t = int(self.overlap*self.bar_width*(i-1) + self.bar_width*self.thickRatio + self.nBarShift*(nbar+1))
                    #         if o>self._stimSize: o -= self._stimSize
                    #         if t>self._stimSize: t -= self._stimSize
                    #         frame2[:, max(0, o):min(self._stimSize, t)] = 1
                    #         frame2 = skiT.rotate(frame2, self.doubleBarRot, order=0)
                    #         frame = np.any(np.stack((frame,frame2), 2), 2)

                    self._stimRaw[it, ...] = skiT.rotate(
                        frame, cross * 360 / self.crossings, order=0
                    )

                    self._stimBase[it] = np.mod(cross, 2) + 1

                    it += 1

                if cross % 2 != 0:
                    it += self.continousBlankLength

            self._create_mask(self._stimRaw.shape)

            self._stimUnc = np.zeros(self._stimRaw.shape)
            self._stimUnc[:, self._stimMask] = self._stimRaw[:, self._stimMask]

    def _checkerboard(self, nChecks=10):
        """create the four flickering main images"""

        # we want at least 1.5 checkers per bar width
        if hasattr(self, "bar_width"):
            self.checkSize = np.min(
                (
                    np.ceil(self._stimSize / nChecks / 2).astype(int),
                    np.ceil(self.bar_width / 1.5),
                )
            ).astype(int)
            self.nChecks = np.ceil(self._stimSize / self.checkSize / 2).astype(int)
        else:
            self.checkSize = np.ceil(self._stimSize / nChecks / 2).astype(int)
            self.nChecks = nChecks

        self.checkA = np.kron(
            [[0, 255] * (self.nChecks + 1), [255, 0] * (self.nChecks + 1)]
            * (self.nChecks + 1),
            np.ones((self.checkSize, self.checkSize)),
        )[
            int(self.checkSize * 3 / 2) : -int(self.checkSize / 2),
            int(self.checkSize / 2) : -int(self.checkSize * 3 / 2),
        ]
        self.checkB = np.kron(
            [[255, 0] * (self.nChecks + 1), [0, 255] * (self.nChecks + 1)]
            * (self.nChecks + 1),
            np.ones((self.checkSize, self.checkSize)),
        )[
            int(self.checkSize * 3 / 2) : -int(self.checkSize / 2),
            int(self.checkSize / 2) : -int(self.checkSize * 3 / 2),
        ]

        self.checkC = np.where(
            skiT.rotate(
                np.kron(
                    [[0, 255] * (self.nChecks + 1), [255, 0] * (self.nChecks + 1)]
                    * (self.nChecks + 1),
                    np.ones((self.checkSize, self.checkSize)),
                ),
                angle=45,
                resize=False,
                order=0,
            )
            < 128,
            0,
            255,
        )[self.checkSize : -self.checkSize, self.checkSize : -self.checkSize]
        self.checkD = np.where(
            skiT.rotate(
                np.kron(
                    [[255, 0] * (self.nChecks + 1), [0, 255] * (self.nChecks + 1)]
                    * (self.nChecks + 1),
                    np.ones((self.checkSize, self.checkSize)),
                ),
                angle=45,
                resize=False,
                order=0,
            )
            < 128,
            0,
            255,
        )[self.checkSize : -self.checkSize, self.checkSize : -self.checkSize]

        if self.checkA.shape[0] != self._stimSize:
            diff = (self.checkA.shape[0] - self._stimSize) / 2
            self.checkA = self.checkA[
                np.floor(diff).astype("int") : -np.ceil(diff).astype("int"),
                np.floor(diff).astype("int") : -np.ceil(diff).astype("int"),
            ]
            self.checkB = self.checkB[
                np.floor(diff).astype("int") : -np.ceil(diff).astype("int"),
                np.floor(diff).astype("int") : -np.ceil(diff).astype("int"),
            ]
        if self.checkC.shape[0] != self._stimSize:
            diff = (self.checkC.shape[0] - self._stimSize) / 2
            self.checkC = self.checkC[
                np.floor(diff).astype("int") : -np.ceil(diff).astype("int"),
                np.floor(diff).astype("int") : -np.ceil(diff).astype("int"),
            ]
            self.checkD = self.checkD[
                np.floor(diff).astype("int") : -np.ceil(diff).astype("int"),
                np.floor(diff).astype("int") : -np.ceil(diff).astype("int"),
            ]

    def stimulus_length(self):
        super().stimulus_length()
        print(f"Frames per crossing: {self.framesPerCrossing} TRs")
        print(f"blanks: {self.nBlanks} x {self.blankLength} TRs")

    def bar_params(self):
        if self.nBars > 1:
            print(f"nBars: {self.nBars}")
            print(f"shift between bars: {self.nBarShift}")
            print(f"bar rotation: {self.doubleBarRot}")
        print(
            f"Bar width: {np.float64(np.round(self.bar_width / self._stimSize * self._maxEcc * 2, 2))}°"
        )
