# Copyright (c) 2017, IGLU consortium
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#  - Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import time
import logging
import numpy as np
import unittest
import matplotlib.pyplot as plt

from panda3d.core import LMatrix4f, LVector3f, TransformState, LVecBase3, BitMask32

from home_platform.physics import Panda3dBulletPhysics
from home_platform.suncg import SunCgSceneLoader, loadModel
from home_platform.utils import Viewer
from home_platform.core import Scene
from home_platform.rendering import Panda3dRenderer

TEST_DATA_DIR = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "..", "data")
TEST_SUNCG_DATA_DIR = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "..", "data", "suncg")


class TestPanda3dBulletPhysics(unittest.TestCase):
    def testStep(self):

        scene = SunCgSceneLoader.loadHouseFromJson(
            "0004d52d1aeeb8ae6de39d6bd993e992", TEST_SUNCG_DATA_DIR)

        physics = Panda3dBulletPhysics(scene)

        for _ in range(10):
            physics.step(dt=0.1)

        physics.destroy()

    def testDebugObjectWithRender(self):

        scene = Scene()

        modelId = '83'
        modelFilename = os.path.join(
            TEST_SUNCG_DATA_DIR, "object", str(modelId), str(modelId) + ".egg")
        assert os.path.exists(modelFilename)
        model = loadModel(modelFilename)
        model.setName('model-' + str(modelId))
        model.hide(BitMask32.allOn())

        objectsNp = scene.scene.attachNewNode('objects')
        objNp = objectsNp.attachNewNode('object-' + str(modelId))
        model.reparentTo(objNp)

        # Calculate the center of this object
        minBounds, maxBounds = model.getTightBounds()
        centerPos = minBounds + (maxBounds - minBounds) / 2.0

        # Add offset transform to make position relative to the center
        model.setTransform(TransformState.makePos(-centerPos))

        renderer = None
        physics = None
        viewer = None

        try:
            renderer = Panda3dRenderer(scene, shadowing=False)
            physics = Panda3dBulletPhysics(scene, debug=True)

            viewer = Viewer(scene, interactive=False)
            viewer.disableMouse()

            viewer.cam.setTransform(
                TransformState.makePos(LVecBase3(5.0, 0.0, 0.0)))
            viewer.cam.lookAt(model)

            for _ in range(20):
                viewer.step()
            time.sleep(1.0)

        finally:
            self.hulkSmash(renderer, physics, viewer)

    def hulkSmash(self, renderer, physics, viewer):
        if renderer is not None:
            renderer.destroy()
        if physics is not None:
            physics.destroy()
        if viewer is not None:
            viewer.destroy()
            viewer.graphicsEngine.removeAllWindows()

    def testDebugHouseWithViewer(self):

        physics = None
        viewer = None

        try:
            scene = SunCgSceneLoader.loadHouseFromJson(
                "0004d52d1aeeb8ae6de39d6bd993e992", TEST_SUNCG_DATA_DIR)

            physics = Panda3dBulletPhysics(
                scene, suncgDatasetRoot=TEST_SUNCG_DATA_DIR, debug=True)

            viewer = Viewer(scene, interactive=False)
            viewer.disableMouse()

            mat = np.array([0.999992, 0.00394238, 0, 0,
                            -0.00295702, 0.750104, -0.661314, 0,
                            -0.00260737, 0.661308, 0.75011, 0,
                            43.621, -55.7499, 12.9722, 1])

            mat = LMatrix4f(*mat.ravel())
            viewer.cam.setMat(mat)
            for _ in range(20):
                viewer.step()
            time.sleep(1.0)

        finally:
            self.hulkSmash(None, physics, viewer)

    def testDebugHouseWithRender(self):
        renderer = None
        physics = None
        viewer = None

        try:
            scene = SunCgSceneLoader.loadHouseFromJson(
                "0004d52d1aeeb8ae6de39d6bd993e992", TEST_SUNCG_DATA_DIR)

            renderer = Panda3dRenderer(
                scene, shadowing=False, mode='offscreen')
            renderer.showRoomLayout(showCeilings=False)

            physics = Panda3dBulletPhysics(
                scene, suncgDatasetRoot=TEST_SUNCG_DATA_DIR, debug=True)

            viewer = Viewer(scene, interactive=False)
            viewer.disableMouse()

            mat = np.array([0.999992, 0.00394238, 0, 0,
                            -0.00295702, 0.750104, -0.661314, 0,
                            -0.00260737, 0.661308, 0.75011, 0,
                            43.621, -55.7499, 12.9722, 1])

            mat = LMatrix4f(*mat.ravel())
            viewer.cam.setMat(mat)
            for _ in range(20):
                viewer.step()
            time.sleep(1.0)

        finally:
            self.hulkSmash(renderer, physics, viewer)

    def testCalculate2dNavigationMap(self):

        scene = SunCgSceneLoader.loadHouseFromJson(
            "0004d52d1aeeb8ae6de39d6bd993e992", TEST_SUNCG_DATA_DIR)

        physics = Panda3dBulletPhysics(scene)

        navMap, _ = physics.calculate2dNavigationMap(
            scene.agents[0], z=1.0, precision=0.1)
        self.assertTrue(np.max(navMap) >= 1.0)

        fig = plt.figure()
        plt.axis("off")
        ax = plt.subplot(111)
        ax.imshow(navMap, cmap='gray')
        plt.show(block=False)
        time.sleep(1.0)
        plt.close(fig)

        physics.destroy()

    def testAgent(self):

        physics = None
        viewer = None

        try:
            scene = Scene()

            physics = Panda3dBulletPhysics(scene, debug=True)

            agent = scene.agents[0].find('**/+BulletRigidBodyNode')
            agent.setPos(LVector3f(0, 0, 1.0))
            agent.node().setLinearVelocity(LVector3f(1, 0, 0))
            agent.node().setAngularVelocity(LVector3f(0, 0, 1))
            agent.node().setActive(True)

            viewer = Viewer(scene, interactive=False)
            viewer.disableMouse()

            mat = np.array([1, 0, 0, 0,
                            0, 1, 0, 0,
                            0, 0, 1, 0,
                            0, -10, 0, 1])
            mat = LMatrix4f(*mat.ravel())
            viewer.cam.setMat(mat)
            for _ in range(50):
                viewer.step()
            time.sleep(1.0)

        finally:
            self.hulkSmash(None, physics, viewer)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN)
    np.seterr(all='raise')
    unittest.main()
