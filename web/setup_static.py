import os
import shutil

def setup_static_files():
    # 创建必要的目录
    static_dirs = [
        'static/img',
        'static/img/logistic_regression',
        'static/img/random_forest',
        'static/img/elo_rating'
    ]
    
    for dir_path in static_dirs:
        os.makedirs(os.path.join(os.path.dirname(__file__), dir_path), exist_ok=True)
    
    # 复制文件映射
    file_mapping = {
        '../model_comparison/model_comparison.png': 'static/img/model_comparison.png',
        '../model_comparison/performance_comparison.png': 'static/img/performance_comparison.png',
        '../logistic_regression/confusion_matrix.png': 'static/img/logistic_regression/confusion_matrix.png',
        '../logistic_regression/feature_importance.png': 'static/img/logistic_regression/feature_importance.png',
        '../random_forest/confusion_matrix.png': 'static/img/random_forest/confusion_matrix.png',
        '../random_forest/feature_importance.png': 'static/img/random_forest/feature_importance.png',
        '../elo_rating/confusion_matrix.png': 'static/img/elo_rating/confusion_matrix.png',
        '../elo_rating/team_ratings.png': 'static/img/elo_rating/team_ratings.png'
    }
    
    # 复制文件
    for src, dst in file_mapping.items():
        src_path = os.path.join(os.path.dirname(__file__), src)
        dst_path = os.path.join(os.path.dirname(__file__), dst)
        try:
            shutil.copy2(src_path, dst_path)
            print(f"已复制: {src} -> {dst}")
        except FileNotFoundError:
            print(f"警告: 未找到文件 {src}")
        except Exception as e:
            print(f"复制 {src} 时出错: {str(e)}")

if __name__ == '__main__':
    setup_static_files() 