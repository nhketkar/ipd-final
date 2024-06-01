def classify_body_type(bust, waist, hip):

    bust_hip_diff = abs(bust - hip)
    bust_waist_diff = abs(bust - waist)
    hip_waist_diff = abs(hip - waist)

    significant_diff =3  # This value can be adjusted

    if bust_hip_diff <= significant_diff and bust_waist_diff > significant_diff and hip_waist_diff > significant_diff:
        return "hourglass"
    elif hip > bust and hip > waist and bust_hip_diff > significant_diff:
        return "pear"
    elif bust_waist_diff <= significant_diff and hip_waist_diff <= significant_diff and bust_hip_diff <= significant_diff:
        return "rectangle"
    elif waist > bust and waist > hip:
        return "apple"
