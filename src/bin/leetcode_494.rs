//! 目标和

pub fn find_target_sum_ways(nums: Vec<i32>, target: i32) -> i32 {
    let len = nums.len();
    let mut result = 0;
    let left = len / 2;
    let right = len - left;
    const NUM: usize = 20000;
    let mut map = vec![0; 2 * NUM];
    for i in 0..1 << left {
        let mut num = 0;
        for j in 0..left {
            if i >> j & 1 == 1 {
                num += nums[j];
            } else {
                num -= nums[j];
            }
        }
        map[(num + NUM as i32) as usize] += 1;
    }
    for i in 0..1 << right {
        let mut num = 0;
        for j in 0..right {
            if i >> j & 1 == 1 {
                num += nums[left + j];
            } else {
                num -= nums[left + j];
            }
        }
        result += map[(target - num + NUM as i32) as usize];
    }
    result
}

/// best
pub fn find_target_sum_ways_best(nums: Vec<i32>, target: i32) -> i32 {
    // 因为nums中的数字num>=0，所以我们可以将填'+'的分为一组，填'-'的分为一组
    // 所有正数（填+）的sum为pos_sum，负数和为neg_sum，有pos_sum + neg_sum = sum(sum为所有数字和)
    // 依照题意, 我们需要          pos_sum - neg_sum = target
    //             =>  (sum - neg_sum) - neg_sum = target
    //             =>          sum - 2 * neg_sum = target
    //             =>                    neg_sum = (sum - target) / 2
    // 问题即转化为在数组nums中寻找数字，使其和为(sum - target) / 2 的方案数

    // 第1步: 计算neg_sum = (sum - target) / 2
    let nums_sum: i32 = nums.iter().sum();
    if nums_sum < target || (nums_sum - target) & 1 != 0 {
        // nums_sum必须比target大
        // sum - target的值必须为偶数，不然(sum - target) / 2为小数，会不合题意（因为nums中都是正整数，其加和无法出现小数）
        // 直接返回0即可
        return 0;
    }

    let neg_sum = (nums_sum - target) >> 1;
    // 下面问题转化为在nums数组中挑选数字，使其和为neg_sum的方案数
    // 设置二维dp表，dp[i][j]表示前i个数字中挑选数字和为j的方案数，最终我们需要的就是dp[nums.len()][neg_sum]
    let mut dp = vec![vec![0; neg_sum as usize + 1]; nums.len() + 1];
    // 初始状态，当i=0（前0个数字、没有数字）时，和只能为0（不选任何数字），所以dp[0][0] = 1, dp[0][j] = 0 (0<j<=neg_sum)
    dp[0][0] = 1;

    // 下面开始进入dp的状态转移
    for i in 1..=nums.len() {
        for j in 0..=neg_sum as usize {
            // 内层，对于每种和，状态转移分以下两种情况
            // 情况1：当前加和小于当前数字(j < nums[i-1])，我们不能放此数字
            //       => dp[i][j] = dp[i-1][j]
            // 情况2：当前加和大于等于当前数字(j >= nums[i-1])，我们可以选择放nums[i-1]也可以选择不放nums[i-1]，总方案数为其加和
            //       => dp[i][j] = dp[i-1][j] + dp[i-1][j-nums[i-1]]
            dp[i][j] = dp[i - 1][j];
            if j >= nums[i - 1] as usize {
                dp[i][j] += dp[i - 1][j - nums[i - 1] as usize]
            }
        }
    }
    dp[nums.len()][neg_sum as usize]
}

fn main() {
    assert_eq!(find_target_sum_ways_best(vec![1, 1, 1, 1, 1], 3), 5);
    assert_eq!(find_target_sum_ways_best(vec![1], 1), 1);
}
