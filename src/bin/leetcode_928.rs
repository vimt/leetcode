//! 尽量减少恶意软件的传播 II


use std::collections::HashSet;

struct UnionSet {
    f: Vec<usize>,
    size: Vec<usize>,
}

impl UnionSet {
    fn new(n: usize) -> Self {
        UnionSet {
            f: (0..n).collect(),
            size: vec![1; n],
        }
    }

    fn find(&mut self, x: usize) -> usize {
        return if self.f[x] == x {
            x
        } else {
            self.f[x] = self.find(self.f[x]);
            self.f[x]
        };
    }

    fn union(&mut self, x: usize, y: usize) {
        let mut xx = self.find(x);
        let mut yy = self.find(y);
        if xx == yy { return; }
        if self.size[xx] > self.size[yy] {
            std::mem::swap(&mut xx, &mut yy);
        }
        self.f[xx] = yy;
        self.size[yy] += self.size[xx];
    }

    fn size(&mut self, x: usize) -> usize {
        let xx = self.find(x);
        self.size[xx]
    }
}

pub fn min_malware_spread(graph: Vec<Vec<i32>>, initial: Vec<i32>) -> i32 {
    let len = graph.len();
    let mut us = UnionSet::new(len);
    let mut init_map = vec![false; len];
    for &idx in &initial {
        init_map[idx as usize] = true;
    }
    for i in 0..len {
        if init_map[i] { continue; }
        for j in i + 1..len {
            if init_map[j] { continue; }
            if graph[i][j] == 1 {
                us.union(i, j);
            }
        }
    }
    let mut rela = vec![HashSet::new(); len];
    let mut rela_cnt = vec![0; len];
    for &idx in &initial {
        let mut set = HashSet::new();
        for i in 0..len {
            if !init_map[i] {
                if graph[idx as usize][i] == 1 {
                    set.insert(us.find(i));
                }
            }
        }
        for &i in &set {
            rela_cnt[i] += 1;
        }
        rela[idx as usize] = set;
    }
    let mut result = 0;
    let mut max_cnt = -1;
    for &idx in &initial {
        let mut remove_cnt = 0;
        for &rela in &rela[idx as usize] {
            if rela_cnt[rela] == 1 {
                remove_cnt += us.size(rela) as i32;
            }
        }
        if remove_cnt > max_cnt || (remove_cnt == max_cnt && idx < result) {
            max_cnt = remove_cnt;
            result = idx;
        }
    }
    result
}

fn main() {
    assert_eq!(min_malware_spread(vec![vec![1, 1, 0], vec![1, 1, 0], vec![0, 0, 1]], vec![0, 1]), 0);
    assert_eq!(min_malware_spread(vec![vec![1, 1, 0], vec![1, 1, 1], vec![0, 1, 1]], vec![0, 1]), 1);
    assert_eq!(min_malware_spread(vec![vec![1, 1, 0, 0], vec![1, 1, 1, 0], vec![0, 1, 1, 1], vec![0, 0, 1, 1]], vec![0, 1]), 1);
}
