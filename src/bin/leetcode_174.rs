//! 三角形最小路径和


/// dp[i][j] 表示[i][j] 到终点所需要的最小血量
pub fn calculate_minimum_hp(dungeon: Vec<Vec<i32>>) -> i32 {
    let m = dungeon.len();
    let n = dungeon[0].len();
    let mut dp = vec![vec![i32::max_value(); n + 1]; m + 1];
    dp[m][n - 1] = 1;
    dp[m - 1][n] = 1;
    for i in (0..m).rev() {
        for j in (0..n).rev() {
            dp[i][j] = 1.max(dp[i + 1][j].min(dp[i][j + 1]) - dungeon[i][j])
        }
    }
    dp[0][0]
}


fn main() {
    assert_eq!(calculate_minimum_hp(vec![vec![2], vec![1]]), 1);
    assert_eq!(calculate_minimum_hp(vec![vec![-2, -3, 3], vec![-5, -10, 1], vec![10, 30, -5]]), 7);
}