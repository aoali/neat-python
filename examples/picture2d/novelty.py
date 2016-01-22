import Image
import random
from multiprocessing import Pool

import numpy as np

from evolve import eval_mono_image, eval_gray_image, eval_color_image
from neat import population, config

width, height = 32, 32
full_scale = 32


def evaluate(genome, scheme):
    if scheme == 'gray':
        return eval_gray_image(genome, width, height)
    elif scheme == 'color':
        return eval_color_image(genome, width, height)
    elif scheme == 'mono':
        return eval_mono_image(genome, width, height)

    raise Exception('Unexpected scheme: {0!r}'.format(scheme))


class NoveltyEvaluator(object):
    def __init__(self, num_workers, scheme):
        self.num_workers = num_workers
        self.scheme = scheme
        self.pool = Pool(num_workers)
        self.archive = []
        self.out_index = 1

    def image_from_array(self, image):
        if self.scheme == 'color':
            return Image.fromarray(image, mode="RGB")

        return Image.fromarray(image, mode="L")

    def evaluate(self, genomes):
        jobs = []
        for genome in genomes:
            jobs.append(self.pool.apply_async(evaluate, (genome, self.scheme)))

        new_archive_entries = []
        for g, j in zip(genomes, jobs):
            image = np.clip(np.array(j.get()), 0, 255).astype(np.uint8)
            float_image = image.astype(np.float32) / 255.0

            g.fitness = (width * height) ** 0.5
            for a in self.archive:
                adist = np.linalg.norm(float_image.ravel() - a.ravel())
                g.fitness = min(g.fitness, adist)

            if random.random() < 0.02:
                new_archive_entries.append(float_image)
                #im = self.image_from_array(image)
                #im.save("novelty-{0:06d}.png".format(self.out_index))

                if self.scheme == 'gray':
                    image = eval_gray_image(g, full_scale * width, full_scale * height)
                elif self.scheme == 'color':
                    image = eval_color_image(g, full_scale * width, full_scale * height)
                elif self.scheme == 'mono':
                    image = eval_mono_image(g, full_scale * width, full_scale * height)
                else:
                    raise Exception('Unexpected scheme: {0!r}'.format(self.scheme))

                im = np.clip(np.array(image), 0, 255).astype(np.uint8)
                im = self.image_from_array(im)
                im.save('novelty-{0:06d}.png'.format(self.out_index))

                self.out_index += 1

        self.archive.extend(new_archive_entries)
        print('{0} archive entries'.format(len(self.archive)))


def run():
    cfg = config.Config('config')
    cfg.pop_size = 100
    cfg.max_fitness_threshold = 1e38

    ne = NoveltyEvaluator(4, 'gray')
    if ne.scheme == 'color':
        cfg.output_nodes = 3
    else:
        cfg.output_nodes = 1

    pop = population.Population(cfg)

    while 1:
        pop.run(ne.evaluate, 1)

        winner = pop.most_fit_genomes[-1]
        if ne.scheme == 'gray':
            image = eval_gray_image(winner, full_scale * width, full_scale * height)
        elif ne.scheme == 'color':
            image = eval_color_image(winner, full_scale * width, full_scale * height)
        elif ne.scheme == 'mono':
            image = eval_mono_image(winner, full_scale * width, full_scale * height)
        else:
            raise Exception('Unexpected scheme: {0!r}'.format(ne.scheme))

        im = np.clip(np.array(image), 0, 255).astype(np.uint8)
        im = ne.image_from_array(im)
        im.save('winning-novelty-{0:06d}.png'.format(pop.generation))

        if ne.scheme == 'gray':
            image = eval_gray_image(winner, width, height)
        elif ne.scheme == 'color':
            image = eval_color_image(winner, width, height)
        elif ne.scheme == 'mono':
            image = eval_mono_image(winner, width, height)
        else:
            raise Exception('Unexpected scheme: {0!r}'.format(ne.scheme))

        float_image = np.array(image, dtype=np.float32) / 255.0
        ne.archive.append(float_image)


if __name__ == '__main__':
    run()