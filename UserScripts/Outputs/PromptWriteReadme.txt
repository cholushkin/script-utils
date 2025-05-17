// --- Source Blob ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\AudioMixer\AudioMixerControllerSingleton.cs ---

using GameLib.Alg;

public class AudioMixerControllerSingleton : SingletonWrapper<AudioMixerController>
{
}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\AudioMixer\AudioMixerControllerSingleton.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\PitchManager.cs ---

using Unity.Mathematics;
using UnityEngine;

/// Adjusts and calculates audio pitch based on original track pitch, time scale, and audio effects.
public class PitchManager : MonoBehaviour
{
    public bool AutoUpdate;
    
    [Header("Time Scale Pitch Settings")]
    [Tooltip("Maximum pitch delta when timeScale is high.")]
    public float MaxTimeScalePitchDelta = 0.3f;

    [Tooltip("Minimum pitch delta when timeScale is low.")]
    public float MinTimeScalePitchDelta = -0.3f;

    [Tooltip("Upper bound of tracked timeScale.")]
    public float MaxTimescaleTracked = 2.0f;

    [Tooltip("Lower bound of tracked timeScale.")]
    public float MinTimescaleTracked = 0.5f;

    private float _sign = 1f;
    private float _trackOriginalPitch = 1f;
    private float _timeScalePitchDelta = 0f;
    private float _effectsPitchDelta = 0f;



    public void Update()
    {
        if (AutoUpdate)
            SetTimeScalePitchDeltaFromTimeScale();
    }
    

    // The final pitch based on all pitch components
    public float Pitch => _sign * (_trackOriginalPitch + _timeScalePitchDelta + _effectsPitchDelta);

    // Sets the pitch sign multiplier (-1 or 1)
    public void SetSign(float sign)
    {
        _sign = math.sign(sign);
        if (_sign == 0f) _sign = 1f;
    }

    // Sets the base/original pitch value
    public void SetTrackOriginalPitch(float pitch) =>
        _trackOriginalPitch = pitch;

    // Manually sets a fixed time scale pitch delta
    public void SetManualTimeScalePitchDelta(float timeScalePitchDelta) =>
        _timeScalePitchDelta = timeScalePitchDelta;

    // Computes pitch delta from current time scale using inspector parameters
    public void SetTimeScalePitchDeltaFromTimeScale() =>
        SetTimeScalePitchDelta(MaxTimeScalePitchDelta, MinTimeScalePitchDelta, MaxTimescaleTracked, MinTimescaleTracked);

    // Sets pitch delta added from audio effects
    public void SetEffectsPitchDelta(float effectsDelta) =>
        _effectsPitchDelta = effectsDelta;
    
    // Computes pitch delta from time scale using custom bounds
    private void SetTimeScalePitchDelta(
        float maxTimeScalePitchDelta,
        float minTimeScalePitchDelta,
        float maxTimescaleTracked,
        float minTimescaleTracked)
    {
        float current = Time.timeScale;
        float clampedTimeScale = math.clamp(current, minTimescaleTracked, maxTimescaleTracked);
        float normalized = math.unlerp(minTimescaleTracked, maxTimescaleTracked, clampedTimeScale);
        _timeScalePitchDelta = math.lerp(minTimeScalePitchDelta, maxTimeScalePitchDelta, normalized);
    }
}


// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\PitchManager.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\TrackPocessorManager\ProcessorSinLowPass.cs ---

using System.Threading;
using Cysharp.Threading.Tasks;
using Unity.Mathematics;
using UnityEngine;

public class ProcessorConfigSinLowPass : TrackProcessorManager.IProcessorConfig
{
    public const string LowPassParameter = "LowPassCutoffFreq";

    public float SinAmplitude = 0.05f;
    public float SinFrequency = 1f;
    public float SinPhase = 0f;
    public float2 LowPassRange; // min, max cutoff frequency
}


public class ProcessorSinLowPass : ProcessorBase<ProcessorConfigSinLowPass>
{
    private ProcessorConfigSinLowPass _config;
    private float _time;

    public override void Initialize(MusicPlayer musicPlayer, AudioMixerController mixer, ProcessorConfigSinLowPass config)
    {
        base.Initialize(musicPlayer, mixer, config);
        _time = 0f;
    }

    public override async UniTask ProcessAsync(CancellationToken token)
    {
        while (!token.IsCancellationRequested)
        {
            _time += Time.deltaTime;

            // Calculate sin wave
            float sinValue = math.sin(2 * math.PI * _config.SinFrequency * _time + _config.SinPhase);
            float t = 0.5f + 0.5f * sinValue * _config.SinAmplitude; // normalized [0,1]

            float cutoffFreq = math.lerp(_config.LowPassRange.x, _config.LowPassRange.y, t);
            
            Mixer.SetParameter(ProcessorConfigSinLowPass.LowPassParameter, cutoffFreq);

            await UniTask.Yield(PlayerLoopTiming.Update, token);
        }
    }
}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\TrackPocessorManager\ProcessorSinLowPass.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicSyncronization\SpectrumAnalyzer.cs ---

using System;
using UnityEngine;
using System.Collections.Generic; 

/// Analyzes audio spectrum and calculates band intensities.
/// Settings are static after Awake.
public class SpectrumAnalyzer : MonoBehaviour
{
    [Serializable]
    public class BandConfiguration
    {
        /// Descriptive name for the band.
        public string BandName = "New Band";

        /// Color used for this band.
        public Color Color = Color.white;

        /// Start frequency in Hz.
        [Range(20f, 20000f)]
        public float StartFrequency = 100f;

        /// End frequency in Hz.
        [Range(20f, 20000f)]
        public float EndFrequency = 500f;

        /// Sensitivity multiplier for intensity.
        [Range(0.0f, 10.0f)]
        public float Sensitivity = 0.5f;

        internal int _bandStartIndex = 0;
        internal int _bandEndIndex = 0;

        /// Calculates spectrum indices.
        public void CalculateIndices(int spectrumSize, float sampleRate)
        {
            float nyquist = sampleRate / 2f;
            if (nyquist <= 0) return;
            float freqPerBin = nyquist / spectrumSize;

            if (freqPerBin <= 0) return;

            float actualStartFreq = Mathf.Min(StartFrequency, EndFrequency);
            float actualEndFreq = Mathf.Max(StartFrequency, EndFrequency);

            _bandStartIndex = Mathf.FloorToInt(actualStartFreq / freqPerBin);
            _bandEndIndex = Mathf.FloorToInt(actualEndFreq / freqPerBin);

            _bandStartIndex = Mathf.Clamp(_bandStartIndex, 0, spectrumSize - 1);
            _bandEndIndex = Mathf.Clamp(_bandEndIndex, _bandStartIndex, spectrumSize - 1);
        }
    }
    #region Unity inspector
    /// AudioSource to analyze.
    public AudioSource AudioSource;

    public bool MergeStereo;

    /// Size of the spectrum array (power of 2).
    [Range(64, 8192)]
    [SerializeField] private int SpectrumSize = 128;

    /// FFT window type.
    [SerializeField] private FFTWindow FftWindow = FFTWindow.BlackmanHarris;

    /// List of frequency bands to analyze.
    public List<BandConfiguration> BandConfigurations = new List<BandConfiguration>();
    #endregion

    /// Raw spectrum data.
    public float[] Spectrum => _spectrum;

    /// Calculated intensity for each band.
    public float[] BandIntensities => _bandIntensities;


    private int _actualSpectrumSize; // Clamped power-of-two size
    private float[] _spectrum; // Main spectrum array
    private float[] _tempSpectrumLeft; // Temp left channel
    private float[] _tempSpectrumRight; // Temp right channel
    private float[] _bandIntensities; // Calculated band intensities

    
    public int GetSpectrumSize() => SpectrumSize;
    public FFTWindow GetFFWindowType() => FftWindow;
    
    #region Unity callbacks
    private void Awake()
    {
        InitializeSpectrum();
    }

    private void Start()
    {
        UpdateBandIndices();
    }

    private void Update()
    {
        if (!Application.isPlaying)
            return;

        int numChannels = AudioSource.clip.channels;
        
        if (numChannels >= 2 && MergeStereo)
        {
            AudioSource.GetSpectrumData(_tempSpectrumLeft, 0, FftWindow);
            AudioSource.GetSpectrumData(_tempSpectrumRight, 1, FftWindow);

            for (int i = 0; i < _actualSpectrumSize; i++)
                _spectrum[i] = (_tempSpectrumLeft[i] + _tempSpectrumRight[i]) * 0.5f;
        }
        else 
            AudioSource.GetSpectrumData(_spectrum, 0, FftWindow);

        CalculateBandIntensities();
    }

    private void Reset()
    {
        MergeStereo = true;
        SpectrumSize = 128;
        AudioSource = GetComponent<AudioSource>();
        
        BandConfigurations = new List<BandConfiguration>
        {
            new BandConfiguration
            {
                BandName = "Bass",
                StartFrequency = 20f,
                EndFrequency = 150f,
                Color = new Color(0.8f, 0.1f, 0.1f, 0.85f), // Deep Red
                Sensitivity = 0.5f
            },
            new BandConfiguration
            {
                BandName = "Middle",
                StartFrequency = 250f,
                EndFrequency = 2000f,
                Color = new Color(1f, 0.5f, 0f, 0.85f), // Orange
                Sensitivity = 0.5f
            },
            new BandConfiguration
            {
                BandName = "High",
                StartFrequency = 2000f,
                EndFrequency = 16000f,
                Color = new Color(0.1f, 0.8f, 0.1f, 0.85f), // Green
                Sensitivity = 0.5f
            }
        };
    }

    
    #endregion

   

    /// Initializes internal spectrum arrays.
    private void InitializeSpectrum()
    {
        _actualSpectrumSize = Mathf.ClosestPowerOfTwo(Mathf.Clamp(SpectrumSize, 64, 8192));

        _spectrum = new float[_actualSpectrumSize];
        _tempSpectrumLeft = new float[_actualSpectrumSize];
        _tempSpectrumRight = new float[_actualSpectrumSize];

        // Initialize band intensities array size based on initial list count
        _bandIntensities = new float[BandConfigurations.Count];
    }

    /// Recalculates spectrum indices.
    private void UpdateBandIndices()
    {
        float sampleRate = AudioSettings.outputSampleRate;

        if (sampleRate <= 0)
             return; // Cannot calculate without valid sample rate

        if (BandConfigurations != null)
        {
            foreach (var band in BandConfigurations)
            {
                if (band != null)
                {
                    band.CalculateIndices(_actualSpectrumSize, sampleRate);
                }
            }
        }
    }

    /// Calculates band intensities from spectrum data.
    private void CalculateBandIntensities()
    {
         for (int i = 0; i < BandConfigurations.Count; i++)
         {
             BandConfiguration band = BandConfigurations[i];

             if (band == null || band._bandEndIndex < band._bandStartIndex)
             {
                 _bandIntensities[i] = 0f;
                 continue;
             }

             int bandBinCount = band._bandEndIndex - band._bandStartIndex + 1;
             float bandIntensity = 0f;

             if (bandBinCount > 0)
             {
                 for (int j = band._bandStartIndex; j <= band._bandEndIndex; j++)
                     if (j >= 0 && j < _spectrum.Length)
                         bandIntensity += _spectrum[j];

                 _bandIntensities[i] = bandIntensity / bandBinCount * band.Sensitivity;
             }
             else
                 _bandIntensities[i] = 0f;
         }
    }
}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicSyncronization\SpectrumAnalyzer.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\TrackPocessorManager\TrackProcessorManager.cs ---

using System.Collections.Generic;
using System.Threading;
using Cysharp.Threading.Tasks;
using UnityEngine;

public class TrackProcessorManager : MonoBehaviour
{
    public interface IProcessorConfig
    {
    }

    public interface ITrackProcessor<in TConfig> where TConfig : IProcessorConfig
    {
        void Initialize(MusicPlayer musicPlayer, AudioMixerController mixer, TConfig config);
        UniTask ProcessAsync(CancellationToken token);
    }

    public MusicPlayer MusicPlayer;
    public AudioMixerController MixerController;

    private readonly List<ITrackProcessor<IProcessorConfig>> _processors = new();
    private CancellationTokenSource _cts;


    #region Unity callbacks

    private void OnDestroy()
    {
        Clear();
    }

    #endregion


    public void AddProcessor<TConfig>(ITrackProcessor<TConfig> processor, TConfig config)
        where TConfig : IProcessorConfig
    {
        if (_cts == null)
        {
            _cts = CancellationTokenSource.CreateLinkedTokenSource(
                this.GetCancellationTokenOnDestroy()
            );
        }

        processor.Initialize(MusicPlayer, MixerController, config);
        processor.ProcessAsync(_cts.Token).Forget();

        _processors.Add(processor as ITrackProcessor<IProcessorConfig>);
    }

    public void Clear()
    {
        _cts?.Cancel();
        _cts?.Dispose();
        _cts = null;
        _processors.Clear(); // no need for individual clears
    }

}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\TrackPocessorManager\TrackProcessorManager.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicConfiguration.cs ---

using System.Collections.Generic;
using NaughtyAttributes;
using TowerGenerator;
using Unity.Mathematics;
using UnityEngine;


[CreateAssetMenu(fileName = "MusicConfiguration", menuName = "Game/MusicConfiguration", order = 1)]
public class MusicConfiguration : ScriptableObject
{
    [System.Serializable]
    public class TrackConfiguration
    {
        public TrackConfiguration()
        {
            // Set default values
            Volume = 1f;
            PitchRange = new float2(0.9f, 1f);
        }

        public bool Included; 
        public AudioClip AudioClip;
        [Range(0f, 2f)]
        public float Volume;
        
        [ShowAsRange] public float2 PitchRange;
        [Tooltip("Possible tags: mood, energy, pop, stars")]
        public TagSet TrackTagset = new(); 
    }
    public List<TrackConfiguration> tracks = new();


    [Button]
    void PrintStats()
    {
        int index = 0;
        foreach (var track in tracks)
        {
            index++;
            if (track.AudioClip == null)
            {
                Debug.LogWarning($"Has no audio clip, index: {index}");
                continue;
            }

            string includedIcon = track.Included ? "✅" : "❌";

            float energy = track.TrackTagset.Get("energy", 0f);
            float mood = track.TrackTagset.Get("mood", 0f);
            float popularity = track.TrackTagset.Get("pop", 0f);
            float stars = track.TrackTagset.Get("stars", 0f);

            string energyDisplay = energy >= 0 ? $"🔥:{energy:F1}" : "";
            string moodDisplay = mood >= 0 ? $"😊:{mood:F1}" : "";
            string popularityDisplay = popularity >= 0 ? $"🎵:{popularity:F1}" : "";
            string starsDisplay = stars > 0 ? $"✨:{stars}" : "";

            Debug.Log($"{includedIcon} {track.AudioClip.name} - " +
                      $"{energyDisplay} {moodDisplay} {popularityDisplay} {starsDisplay}".Trim());
        }
    }

}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicConfiguration.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\AudioSourceExtension.cs ---

using System;
using System.Threading;
using Cysharp.Threading.Tasks;
using UnityEngine;

public static class AudioSourceExtension
{
    /// <summary>
    /// Fades an AudioSource's volume from <paramref name="from"/> to <paramref name="to"/>
    /// over <paramref name="duration"/> seconds.  
    /// Pauses the fade if <paramref name="isPaused"/> returns true.
    /// </summary>
    public static async UniTask FadeVolumeAsync(
        this AudioSource source,
        float from,
        float to,
        float duration,
        Func<bool> isPaused,
        CancellationToken token = default
    )
    {
        float elapsed = 0f;
        source.volume = from;

        while (elapsed < duration && !token.IsCancellationRequested)
        {
            if (isPaused())
            {
                await UniTask.Yield(PlayerLoopTiming.Update, token);
                continue;
            }

            elapsed += Time.deltaTime;
            float t = Mathf.Clamp01(elapsed / duration);
            source.volume = Mathf.Lerp(from, to, t);
            await UniTask.Yield(PlayerLoopTiming.Update, token);
        }

        source.volume = to;
    }
    
    public static async UniTask RampParamAsync(
        this AudioMixerController mixer,
        string parameterName,
        float from,
        float to,
        float duration,
        Func<bool> isPaused,
        CancellationToken token = default
    )
    {
        float elapsed = 0f;

        while (elapsed < duration && !token.IsCancellationRequested)
        {
            if (isPaused())
            {
                await UniTask.Yield(PlayerLoopTiming.Update, token);
                continue;
            }

            elapsed += Time.deltaTime;
            float t = Mathf.Clamp01(elapsed / duration);
            float value = Mathf.Lerp(from, to, t);
            mixer.SetParameter(parameterName, value);
            await UniTask.Yield(PlayerLoopTiming.Update, token);
        }

        mixer.SetParameter(parameterName, to);
    }
}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\AudioSourceExtension.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\AudioMixer\AudioMixerController.cs ---

using UnityEngine;
using UnityEngine.Audio;

public class AudioMixerController : MonoBehaviour
{
    [SerializeField] private AudioMixer mixer;

    public void SetParameter(string parameterName, float value) => mixer.SetFloat(parameterName, value);
    public bool TryGetParameter(string parameterName, out float value) => mixer.GetFloat(parameterName, out value);
}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\AudioMixer\AudioMixerController.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicSyncronization\SpectrumRawVisualization.cs ---

using UnityEngine;
using UnityEngine.UI;

[RequireComponent(typeof(RectTransform))]
public class SpectrumRawVisualization : Graphic
{
    public SpectrumAnalyzer SpectrumAnalyzer;

    [Header("Visualization Settings")]
    public float HeightScale;

    public Color BarColor = Color.green;

    private void Update()
    {
        SetVerticesDirty();
    }

    protected override void Reset()
    {
        base.Reset();
        HeightScale = 8;
    }
    
    protected override void OnPopulateMesh(VertexHelper vh)
    {
        vh.Clear();

        if (SpectrumAnalyzer == null || SpectrumAnalyzer.Spectrum == null)
            return;

        float[] spectrum = SpectrumAnalyzer.Spectrum;
        int count = spectrum.Length;

        Rect rect = GetPixelAdjustedRect();

        // Draw inner background rectangle
        AddQuad(vh,
            new Vector2(rect.xMin, rect.yMin),
            new Vector2(rect.xMax, rect.yMax),
            color);

        // Draw spectrum bars
        float barWidth = rect.width / count;

        for (int i = 0; i < count; i++)
        {
            float value = Mathf.Clamp01(spectrum[i] * HeightScale);
            float barHeight = value * rect.height;

            float x0 = rect.xMin + i * barWidth;
            float x1 = x0 + barWidth;
            float y0 = rect.yMin;
            float y1 = y0 + barHeight;

            AddQuad(vh, new Vector2(x0, y0), new Vector2(x1, y1), BarColor);
        }
    }

    private static void AddQuad(VertexHelper vh, Vector2 bottomLeft, Vector2 topRight, Color32 color)
    {
        int i = vh.currentVertCount;

        vh.AddVert(new Vector3(bottomLeft.x, bottomLeft.y), color, Vector2.zero);
        vh.AddVert(new Vector3(bottomLeft.x, topRight.y), color, Vector2.zero);
        vh.AddVert(new Vector3(topRight.x, topRight.y), color, Vector2.zero);
        vh.AddVert(new Vector3(topRight.x, bottomLeft.y), color, Vector2.zero);

        vh.AddTriangle(i + 0, i + 1, i + 2);
        vh.AddTriangle(i + 2, i + 3, i + 0);
    }
}


// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicSyncronization\SpectrumRawVisualization.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\TrackPocessorManager\ProcessorBase.cs ---

using System.Threading;
using Cysharp.Threading.Tasks;
using FuzzySharp.Utils;
using UnityEngine;

public abstract class ProcessorBase<TConfig> : TrackProcessorManager.ITrackProcessor<TConfig>
    where TConfig : TrackProcessorManager.IProcessorConfig
{
    protected AudioSource Source;
    protected MusicPlayer MusicPlayer;
    protected TConfig Config;
    protected AudioMixerController Mixer;

    public virtual void Initialize(MusicPlayer musicPlayer, AudioMixerController mixer, TConfig config)
    {
        MusicPlayer = musicPlayer;
        Source = MusicPlayer.Source;
        Config = config;
        Mixer = mixer;
    }

    public abstract UniTask ProcessAsync(CancellationToken token);
}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\TrackPocessorManager\ProcessorBase.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicPlayerSingleton.cs ---

using GameLib.Alg;

public class MusicPlayerSingleton : SingletonWrapper<MusicPlayer>
{
}


// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicPlayerSingleton.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicSyncronization\BeatPulseUnitVisualization.cs ---

using UnityEngine;
using UnityEngine.UI;

[RequireComponent(typeof(RectTransform))]
public class BeatPulseUnitVisualization : Graphic
{
    public BeatPulseUnit BeatUnit;

    [Header("Visualization Settings")]
    public float HeightScale = 8f;
    public Color32 ThresholdLineColor = Color.red;
    public float ThresholdLineThickness = 4f;

    protected override void OnPopulateMesh(VertexHelper vh)
    {
        vh.Clear();

        if (BeatUnit == null || BeatUnit.SpectrumAnalyzer == null)
            return;

        var analyzer = BeatUnit.SpectrumAnalyzer;
        var intensities = analyzer.BandIntensities;
        var bands = analyzer.BandConfigurations;

        if (!Application.isPlaying || intensities == null || bands == null)
            return;

        if (BeatUnit.BandIndex < 0 || BeatUnit.BandIndex >= intensities.Length)
            return;

        Rect rect = GetPixelAdjustedRect();

        // Background (optional)
        AddQuad(vh,
            new Vector2(rect.xMin, rect.yMin),
            new Vector2(rect.xMax, rect.yMax),
            color);

        // Draw vertical bar for selected band (raw intensity)
        float rawValue = Mathf.Clamp01(intensities[BeatUnit.BandIndex] * HeightScale);
        float rawBarHeight = rawValue * rect.height;
        Color32 bandColor = bands[BeatUnit.BandIndex].Color;

        AddQuad(vh,
            new Vector2(rect.xMin, rect.yMin),
            new Vector2(rect.xMax, rect.yMin + rawBarHeight),
            Color.Lerp(bandColor, Color.white, 0.8f));

        // Draw smoothed value bar (narrower, on top)
        float smoothedValue = Mathf.Clamp01(BeatUnit.SmoothedValue * HeightScale);
        float smoothedHeight = smoothedValue * rect.height;

        float halfBarWidth = rect.width * 0.25f;
        float centerX = rect.xMin + rect.width * 0.5f;

        AddQuad(vh,
            new Vector2(centerX - halfBarWidth * 0.5f, rect.yMin),
            new Vector2(centerX + halfBarWidth * 0.5f, rect.yMin + smoothedHeight),
            Color.Lerp(bandColor, Color.white, 0.5f)); 
        
        
        // Draw sin value bar (narrower, on top)
        float sinValue = Mathf.Clamp01(BeatUnit.SinValue * HeightScale);
        float sinHeight = sinValue * rect.height;
        AddQuad(vh,
            new Vector2(centerX - halfBarWidth * 0.25f, rect.yMin),
            new Vector2(centerX + halfBarWidth * 0.25f, rect.yMin + sinHeight),
            Color.Lerp(bandColor, Color.white, 0.85f)); 

        // Draw horizontal threshold line
        float thresholdY = rect.yMin + (BeatUnit.Threshold * HeightScale * rect.height);

        AddQuad(vh,
            new Vector2(rect.xMin, thresholdY - ThresholdLineThickness * 0.5f),
            new Vector2(rect.xMax, thresholdY + ThresholdLineThickness * 0.5f),
            BeatUnit.IsBeat ? Color.white : ThresholdLineColor);
    }

    private static void AddQuad(VertexHelper vh, Vector2 bottomLeft, Vector2 topRight, Color32 color)
    {
        int i = vh.currentVertCount;

        vh.AddVert(new Vector3(bottomLeft.x, bottomLeft.y), color, Vector2.zero);
        vh.AddVert(new Vector3(bottomLeft.x, topRight.y), color, Vector2.zero);
        vh.AddVert(new Vector3(topRight.x, topRight.y), color, Vector2.zero);
        vh.AddVert(new Vector3(topRight.x, bottomLeft.y), color, Vector2.zero);

        vh.AddTriangle(i + 0, i + 1, i + 2);
        vh.AddTriangle(i + 2, i + 3, i + 0);
    }

    private void Update()
    {
        SetVerticesDirty();
    }
}


// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicSyncronization\BeatPulseUnitVisualization.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicSyncronization\SpectrumBandsVisualization.cs ---

using UnityEngine;
using UnityEngine.UI;

[RequireComponent(typeof(RectTransform))]
public class SpectrumBandsVisualization : Graphic
{
    public SpectrumAnalyzer SpectrumAnalyzer;

    [Header("Visualization Settings")]
    [SerializeField] private float HeightScale = 8f;

    protected override void OnPopulateMesh(VertexHelper vh)
    {
        vh.Clear();

        if (SpectrumAnalyzer == null || SpectrumAnalyzer.BandIntensities == null)
            return;
        
        if(!Application.isPlaying)
            return;

        var bands = SpectrumAnalyzer.BandConfigurations;
        var intensities = SpectrumAnalyzer.BandIntensities;
        int count = bands.Count;

        Rect rect = GetPixelAdjustedRect();

        // Background rect
        AddQuad(vh,
            new Vector2(rect.xMin, rect.yMin),
            new Vector2(rect.xMax, rect.yMax),
            color);

        if (count == 0) return;

        float bandWidth = rect.width / count;

        for (int i = 0; i < count; i++)
        {
            var band = bands[i];
            float value = Mathf.Clamp01(intensities[i] * HeightScale);
            float barHeight = value * rect.height;

            float x0 = rect.xMin + i * bandWidth;
            float x1 = x0 + bandWidth;
            float y0 = rect.yMin;
            float y1 = y0 + barHeight;

            AddQuad(vh, new Vector2(x0, y0), new Vector2(x1, y1), band.Color);
        }
    }

    private static void AddQuad(VertexHelper vh, Vector2 bottomLeft, Vector2 topRight, Color32 color)
    {
        int i = vh.currentVertCount;

        vh.AddVert(new Vector3(bottomLeft.x, bottomLeft.y), color, Vector2.zero);
        vh.AddVert(new Vector3(bottomLeft.x, topRight.y), color, Vector2.zero);
        vh.AddVert(new Vector3(topRight.x, topRight.y), color, Vector2.zero);
        vh.AddVert(new Vector3(topRight.x, bottomLeft.y), color, Vector2.zero);

        vh.AddTriangle(i + 0, i + 1, i + 2);
        vh.AddTriangle(i + 2, i + 3, i + 0);
    }

    private void Update()
    {
        SetVerticesDirty();
    }
}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicSyncronization\SpectrumBandsVisualization.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicSyncronization\BeatPulseUnit.cs ---

using UnityEngine;
using UnityEngine.Events;
using UnityEngine.Serialization;

/// <summary>
/// Detects beats in a single band of a SpectrumAnalyzer, based on threshold and timing logic.
/// Fires OnBeat events for others to respond to.
/// </summary>
public class BeatPulseUnit : MonoBehaviour
{
    [Header("Additional Sin Signal")]
    [Tooltip("Enable or disable sine wave modulation.")]
    public bool UseSinSignal = false;

    [Tooltip("Amplitude of the sine wave added to the raw input.")]
    [Range(0f,0.1f)]
    public float SinAmplitude = 0.05f;

    [Tooltip("Frequency of the sine wave in Hz.")]
    public float SinFrequency = 1f;
    
    [Tooltip("Optional phase offset (in seconds).")]
    public float SinPhase = 0f;

    [Tooltip("Blend factor between original input and sine-modulated value (0 = only input, 1 = only sine).")]
    [Range(0f, 1f)]
    public float SinBlend = 0f;
    
    [Header("Spectrum Input")] public SpectrumAnalyzer SpectrumAnalyzer;
    [Range(0, 31)] public int BandIndex = 0;

    [Header("Beat Detection Parameters")] [Tooltip("Threshold above which a beat is triggered.")]
    [Range(0f, 0.5f)]
    public float Threshold = 0.1f;

    [Tooltip("Minimum interval between beats (in seconds).")]
    public float MinInterval = 0.2f;

    [Header("BPM Damping")] [Tooltip("Approximate BPM to smooth response (affects damping only).")]
    public float BPM = 80f;

    [Tooltip("Lerp factor for smoothing the band intensity.")] [Range(0f, 1f)]
    public float Damping = 0.3f;

    [Header("Output Event")] public UnityEvent OnBeat;

    private float _previousValue;
    public float SmoothedValue { get; private set; }
    public float SinValue { get; private set; }
    private float _timer;

    public bool IsBeat { get; private set; }
    
    
    
    [Header("Adaptive Threshold")]
    public bool UseAdaptiveThreshold = false;

    [Tooltip("User-defined base threshold (used when adaptive is off).")]
    [Range(0f, 1f)]
    public float BaseThreshold = 0.1f;

    [Tooltip("How sensitive the adaptive threshold is (higher = closer to peaks).")]
    [Range(0f, 1f)]
    public float ThresholdSensitivity = 0.7f;

    private float _runningAverage;
    private float _runningPeak;

    private void Reset()
    {
        BaseThreshold = 0.15f;
        Threshold = BaseThreshold;
        MinInterval = 0.25f;
        BPM = 80;
        Damping = 0.2f;
        ThresholdSensitivity = 0.7f;
    }

    public float GetValue()
    {
        return SmoothedValue * 10f;
    }


    private void Update()
    {
        if (SpectrumAnalyzer == null || SpectrumAnalyzer.BandIntensities == null || BandIndex >= SpectrumAnalyzer.BandIntensities.Length)
            return;

        float rawValue = SpectrumAnalyzer.BandIntensities[BandIndex];

        SinValue = (Mathf.Sin((Time.time + SinPhase) * SinFrequency * 2f * Mathf.PI) + 1f) * 0.5f * SinAmplitude;

        if (UseSinSignal)
            rawValue = Mathf.Lerp(rawValue, rawValue + SinValue, SinBlend);

        // Smooth the input
        SmoothedValue = Mathf.Lerp(SmoothedValue, rawValue, 1f - Mathf.Pow(1f - Damping, Time.deltaTime * BPM / 60f));

        // Update running stats
        _runningAverage = Mathf.Lerp(_runningAverage, SmoothedValue, 0.05f);
        _runningPeak = Mathf.Max(_runningPeak * 0.95f, SmoothedValue);

        if (UseAdaptiveThreshold)
        {
            Threshold = _runningAverage + (_runningPeak - _runningAverage) * ThresholdSensitivity;
        }
        else
        {
            Threshold = BaseThreshold;
        }

        // Beat detection logic
        bool overThreshold = SmoothedValue >= Threshold;

        if (_timer >= MinInterval)
        {
            IsBeat = false;
            if (overThreshold)
            {
                _timer = 0f;
                IsBeat = true;
                OnBeat?.Invoke();
            }
        }

        _timer += Time.deltaTime;
    }

}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicSyncronization\BeatPulseUnit.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\TrackPocessorManager\ProcessorBizarreLoop.cs ---

using System;
using System.Threading;
using Cysharp.Threading.Tasks;
using UnityEngine;
using UnityEngine.Assertions;

// ProcessorBizarreLoop alternates between normal and reverse playback modes:
// 1. Play the track forward from time = 0 at normal pitch.
// 2. Fade in volume using FadeInDuration.
// 3. As the track approaches the end, begin fading out using FadeOutDuration.
// 4. When fade-out completes, jump to ReverseDuration seconds from the beginning.
// 5. Reverse playback using negative original pitch.
// 6. Fade in using ReverseFadeInDuration.
// 7. As the track approaches the beginning, begin fading out using ReverseFadeOutDuration.
// 8. When reverse playback hits time = 0, loop back to step 1.
//
// Echo behavior (loop > 1):
// - On transitions from reverse to forward, echo fades out (EchoWetMix 1→0) simultaneously with volume fade-in.
// - On transitions from forward to reverse, echo fades in (EchoWetMix 0→1) simultaneously with reverse fade-in volume.
//
// The track endlessly alternates between forward and reverse playback with smooth crossfading and synchronized echo transitions.

public class ProcessorConfigBizarreLoop : TrackProcessorManager.IProcessorConfig
{
    public float FadeInDuration = 0f; // Fade in at start of normal playback
    public float FadeOutDuration = 4f; // Fade out near end of normal playback
    public float ReverseFadeInDuration = 4f; // Fade in when starting reverse playback
    public float ReverseFadeOutDuration = 0f; // Fade out when approaching beginning in reverse
    public float ReverseDuration = 12f; // How far from beginning to jump for reverse playback

    public float TrackOriginalPitch = 1f;

    [Tooltip("How long to ramp the echo wet mix when switching direction")]
    public float EchoDuration = 3f;
}


public class ProcessorBizarreLoop : ProcessorBase<ProcessorConfigBizarreLoop>
{
    private int _loopCount;

    public override void Initialize(MusicPlayer musicPlayer, AudioMixerController mixer, ProcessorConfigBizarreLoop config)
    {
        base.Initialize(musicPlayer, mixer, config);
        Assert.IsFalse(Source.loop, "Loop must be off");
        Assert.IsTrue(config.ReverseDuration > config.ReverseFadeInDuration);
    }

    public override async UniTask ProcessAsync(CancellationToken token)
    {
        while (!token.IsCancellationRequested)
        {
            _loopCount++;

            // Forward playback setup: reset pitch, time, and volume
            Source.pitch = Config.TrackOriginalPitch;
            Source.time = 0f;
            Source.volume = 0f;

            var clip = Source.clip;
            if (clip == null)
                throw new InvalidOperationException("No AudioClip assigned to source.");

            // Start forward playback immediately to allow overlap with echo ramp
            Source.Play();
            await UniTask.Yield(PlayerLoopTiming.Update, token);

            // On loops > 1, fade echo out simultaneously with fade-in volume
            if (_loopCount > 1)
            {
                var echoFadeTask = AudioSourceExtension.RampParamAsync(
                    Mixer,
                    "EchoWetMix",
                    1f, 0f,
                    Config.EchoDuration,
                    () => MusicPlayer.IsPaused);

                var volumeFadeTask = Source.FadeVolumeAsync(
                    0f, 1f, Config.FadeInDuration,
                    () => MusicPlayer.IsPaused,
                    token);

                await UniTask.WhenAll(echoFadeTask, volumeFadeTask);
            }
            else
            {
                // Initial loop: just fade in volume
                await Source.FadeVolumeAsync(
                    0f, 1f, Config.FadeInDuration,
                    () => MusicPlayer.IsPaused,
                    token);
            }

            float fadeOutStart = Mathf.Clamp(clip.length - Config.FadeOutDuration, 0f, clip.length);
            await WaitUntilTime(fadeOutStart, token);

            if (Config.FadeOutDuration > 0f)
            {
                await Source.FadeVolumeAsync(
                    1f, 0f, Config.FadeOutDuration,
                    () => MusicPlayer.IsPaused,
                    token);
            }

            await WaitUntilPlayToEnd(token);
            Source.Stop();

            // Reverse playback setup
            float reverseStart = Mathf.Clamp(Config.ReverseDuration, 0f, clip.length);
            Source.pitch = -Config.TrackOriginalPitch;
            Source.time = reverseStart;
            Source.volume = 0f;

            // Start reverse playback immediately
            Source.Play();
            await UniTask.Yield(PlayerLoopTiming.Update, token);

            // Echo in reverse playback (linearly 0 -> 1)
            var reverseEchoTask = AudioSourceExtension.RampParamAsync(
                Mixer,
                "EchoWetMix",
                0f, 1f,
                Config.EchoDuration,
                () => MusicPlayer.IsPaused);

            var reverseFadeInTask = Source.FadeVolumeAsync(
                0f, 1f, Config.ReverseFadeInDuration,
                () => MusicPlayer.IsPaused,
                token);

            await UniTask.WhenAll(reverseEchoTask, reverseFadeInTask);

            // Wait until near the beginning
            float reverseFadeThreshold = Mathf.Clamp(Config.ReverseFadeOutDuration, 0f, reverseStart);
            await WaitUntilTimeReverse(reverseFadeThreshold, token);

            if (Config.ReverseFadeOutDuration > 0f)
            {
                await Source.FadeVolumeAsync(
                    1f, 0f, Config.ReverseFadeOutDuration,
                    () => MusicPlayer.IsPaused,
                    token);
            }

            await WaitUntilPlayToEnd(token);
            Source.Stop();
        }
    }
    
    // Wait until source is neither playing nor paused
    private async UniTask WaitUntilPlayToEnd(CancellationToken token)
    {
        while ((Source.isPlaying || MusicPlayer.IsPaused)
               && !token.IsCancellationRequested)
        {
            await UniTask.Yield(PlayerLoopTiming.Update, token);
        }
    }


    private async UniTask FadeVolume(AudioSource source, float from, float to, float duration, CancellationToken token)
    {
        Debug.Log($"fade {from} {to}");
        float t = 0f;
        while (t < duration && !token.IsCancellationRequested)
        {
            t += Time.deltaTime;
            source.volume = Mathf.Lerp(from, to, t / duration);
            await UniTask.Yield(PlayerLoopTiming.Update, token);
        }

        source.volume = to;
    }

    private async UniTask WaitUntilTime(float targetTime, CancellationToken token)
    {
        while ((Source.isPlaying || MusicPlayer.IsPaused) && Source.time < targetTime && !token.IsCancellationRequested)
            await UniTask.Yield(PlayerLoopTiming.Update, token);
    }

    private async UniTask WaitUntilTimeReverse(float targetTime, CancellationToken token)
    {
        while ((Source.isPlaying || MusicPlayer.IsPaused) && Source.time > targetTime && !token.IsCancellationRequested)
            await UniTask.Yield(PlayerLoopTiming.Update, token);
    }
}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\TrackPocessorManager\ProcessorBizarreLoop.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\TrackPocessorManager\ProcessorStandardLoop.cs ---

using System.Threading;
using Cysharp.Threading.Tasks;
using UnityEngine;

public class ProcessorConfigStandardLoop : TrackProcessorManager.IProcessorConfig
{
    public float FadeOutDuration = 2f; // Seconds before end
    public float FadeInDuration = 2f; // Seconds at beginning
}

public class ProcessorStandardLoop : ProcessorBase<ProcessorConfigStandardLoop>
{
    private AudioSource _source;
    private ProcessorConfigStandardLoop _config;
    private MusicPlayer _musicPlayer;

    public override async UniTask ProcessAsync(CancellationToken cancellationToken)
    {
        // Loop until the token is cancelled
        while (!cancellationToken.IsCancellationRequested)
        {
            // Don’t start a track while paused
            while (_musicPlayer.IsPaused && !cancellationToken.IsCancellationRequested)
                await UniTask.Yield(PlayerLoopTiming.Update, cancellationToken);

            if (cancellationToken.IsCancellationRequested)
                break;

            // Start playback if needed
            if (!_source.isPlaying)
            {
                _source.time = 0f;
                _source.volume = 0f;
                _source.Play();
            }

            // Fade-in
            await _source.FadeVolumeAsync(
                0f, 1f, _config.FadeInDuration,
                () => _musicPlayer.IsPaused,
                cancellationToken
            );

            // Wait for fade-out moment or pause
            while ((_source.isPlaying || _musicPlayer.IsPaused)
                   && !cancellationToken.IsCancellationRequested)
            {
                float remaining = _source.clip.length - _source.time;
                if (_config.FadeOutDuration > 0f && remaining <= _config.FadeOutDuration)
                {
                    await _source.FadeVolumeAsync(
                        _source.volume, 0f, remaining,
                        () => _musicPlayer.IsPaused,
                        cancellationToken
                    );
                    break;
                }

                await UniTask.Yield(PlayerLoopTiming.Update, cancellationToken);
            }

            // Stop & reset for next iteration
            _source.Stop();
            _source.time = 0f;
            _source.volume = 0f;
        }
    }
}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\TrackPocessorManager\ProcessorStandardLoop.cs ---

// --- Start File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicPlayer.cs ---

using System;
using System.Linq;
using System.Threading;
using Cysharp.Threading.Tasks;
using GameLib.Algorythms;
using GameLib.Random;
using NaughtyAttributes;
using UnityEngine;
using UnityEngine.Assertions;
using Random = GameLib.Random.Random;

public class MusicPlayer : MonoBehaviour
{
    public struct EventPlayTrack
    {
        public AudioSource AudioSource;
    }

    public bool IsPaused { get; set; }
    public bool PlayOnStart;
    public AudioSource Source;
    public MusicConfiguration MusicConfiguration;
    public AudioMixerController Mixer;
    public PitchManager PitchManager;
    [Tooltip("Set 0 to randomize seed")] public uint SeedTrackSelecting;
    
    [Tooltip("Fade out duration for track switch")]
    public float FadeOutDuration = 2f;

    public TrackProcessorManager TrackProcessorManager;
    private Random _rngTrackSelector;
    private CircularBuffer<int> _trackHistory = new CircularBuffer<int>(HistoryCapacity);
    private int _historyPointer = -1;
    
    private const int HistoryCapacity = 64;
    private CancellationTokenSource _playCts;
    private UniTask _playTask = UniTask.CompletedTask;



    void Awake()
    {
        _rngTrackSelector = SeedTrackSelecting == 0 ? RandomHelper.CreateRandomNumberGenerator(out SeedTrackSelecting) : RandomHelper.CreateRandomNumberGenerator(SeedTrackSelecting);
        Assert.IsNotNull(TrackProcessorManager);
    }

    void Start()
    {
        if (PlayOnStart)
            PlayNextRandom();
    }

    public void PlayItem(MusicConfiguration.TrackConfiguration cfg)
    {
        DebounceAndPlay(cfg).Forget();
    }
    
    // Set all modulation parameters for music tracks
    // But pitch of time machine is still not touched
    public void CleanModulationForEffectProcessors()
    {
        Mixer.SetParameter("EchoWetMix", 0f);
        Mixer.SetParameter("LowPassCutoffFreq", 220000f);
        Source.pitch = 1f;
        Source.volume = 1f;
    }
    
    
    // This handles cancelling the old, awaiting its teardown, then starting the new
    private async UniTaskVoid DebounceAndPlay(MusicConfiguration.TrackConfiguration cfg)
    {
        // Cancel the previous in‐flight PlayItemAsync
        _playCts?.Cancel();

        // Wait for it to actually tear down (or get cancelled)
        try
        {
            await _playTask;
        }
        catch (OperationCanceledException)
        {
            // swallow the cancellation, that’s expected
        }

        // Now start the new one
        _playCts   = new CancellationTokenSource();
        _playTask  = PlayItemAsync(cfg, _playCts.Token);
    }
    
    private async UniTask PlayItemAsync(
        MusicConfiguration.TrackConfiguration configurationItem,
        CancellationToken cancellationToken = default
    )
    {
        if (configurationItem == null || configurationItem.AudioClip == null)
        {
            Debug.LogError("PlayItem: configuration or AudioClip was null.");
            return;
        }

        // Cancel existing processors (don't reset parameters yet)
        TrackProcessorManager.Clear();

        // Wait briefly to ensure processors have exited their logic loops
        await UniTask.Yield(PlayerLoopTiming.Update);

        // Fade out current track with existing parameters
        if (Source.clip != null && Source.isPlaying)
        {
            await Source.FadeVolumeAsync(
                Source.volume,
                0f,
                FadeOutDuration,
                () => IsPaused,
                cancellationToken
            );
            Source.Stop();
        }

        // Explicitly reset all modulation parameters to defaults
        CleanModulationForEffectProcessors();

        // Set up the next track
        Source.clip = configurationItem.AudioClip;
        Source.volume = 1f;
        Source.pitch = RandomHelper.Rng.Range(configurationItem.PitchRange);

        // Configure processors
        SetupProcessorsFor(configurationItem);
    
        // Start playing new track
        Source.Play();
        GlobalEventAggregator.EventAggregator.Publish(
            new EventPlayTrack { AudioSource = Source }
        );
    }

    // If-Factory
    private void SetupProcessorsFor(MusicConfiguration.TrackConfiguration cfg)
    {
        // StandardLoop is always on:
        // TrackProcessorManager.AddProcessor(
        //     new ProcessorStandardLoop(),
        //     new ProcessorConfigStandardLoop
        //     {
        //         FadeInDuration  = 0f,
        //         FadeOutDuration = FadeOutDuration
        //     }
        // );
        
        TrackProcessorManager.AddProcessor(
            new ProcessorBizarreLoop(),
            new ProcessorConfigBizarreLoop
            {
                FadeInDuration = 0f,
                FadeOutDuration = 4f,
                ReverseFadeInDuration =  4f,
                ReverseFadeOutDuration = 0.2f,
                ReverseDuration = 12f,
                TrackOriginalPitch = Source.pitch
            }
        );

        // If you had other flags on cfg you could do:
        // if (cfg.EnableBizarre) {
        //     TrackProcessorManager.AddProcessor(
        //         new ProcessorBizarreLoop(),
        //         new ProcessorConfigBizarreLoop { /*…*/ }
        //     );
        // }
        //
        // if (cfg.UseLowPass) {
        //     TrackProcessorManager.AddProcessor(
        //         new ProcessorSinLowPass(),
        //         new ProcessorConfigSinLowPass { /*…*/ }
        //     );
        // }
    }

    private async UniTask FadeVolume(float from, float to, float duration, CancellationToken token)
    {
        float elapsed = 0f;
        Source.volume = from;

        while (elapsed < duration && !token.IsCancellationRequested)
        {
            // pause-aware stall
            if (IsPaused)
            {
                await UniTask.Yield(PlayerLoopTiming.Update, token);
                continue;
            }

            elapsed += Time.deltaTime;
            float t = Mathf.Clamp01(elapsed / duration);
            Source.volume = Mathf.Lerp(from, to, t);
            await UniTask.Yield(PlayerLoopTiming.Update, token);
        }

        Source.volume = to;
    }

    [Button]
    public void PlayNextHistory()
    {
        if (_trackHistory.Count == 0 || _historyPointer >= _trackHistory.Count - 1)
        {
            Debug.Log("No next track in history.");
            return;
        }

        _historyPointer++;
        int trackIndex = _trackHistory[_historyPointer];
        PlayItem(MusicConfiguration.tracks[trackIndex]);
    }

    [Button]
    public void PlayPreviousHistory()
    {
        if (_trackHistory.Count == 0 || _historyPointer <= 0)
        {
            Debug.Log("No previous track in history.");
            return;
        }

        _historyPointer--;
        int trackIndex = _trackHistory[_historyPointer];
        PlayItem(MusicConfiguration.tracks[trackIndex]);
    }

    [Button]
    public void PlayNextRandom()
    {
        var included = MusicConfiguration.tracks.Where(t => t.Included).ToList();
        if (included.Count == 0)
        {
            Debug.LogWarning("No tracks included in configuration.");
            return;
        }

        var configurationItem = _rngTrackSelector.FromList(included);
        int index = MusicConfiguration.tracks.IndexOf(configurationItem);

        _trackHistory.Enqueue(index);
        _historyPointer = _trackHistory.Count - 1;

        PlayItem(configurationItem);
    }

    [Button]
    public void Pause()
    {
        Source.Pause();
        IsPaused = true;
    }

    [Button]
    public void Resume()
    {
        Source.UnPause();
        IsPaused = false;
    }

    public void Rewind(float seconds)
    {
        Source.time = Mathf.Max(Source.time - seconds, 0f);
    }

    public void Forward(float seconds)
    {
        Source.time = Mathf.Min(Source.time + seconds, Source.clip.length);
    }

    [Button]
    public void DbgPrintHistory()
    {
        if (_trackHistory.Count == 0)
        {
            Debug.Log("History is empty.");
            return;
        }

        var output = "Track History:\n";
        for (int i = 0; i < _trackHistory.Count; i++)
        {
            int index = _trackHistory[i];
            var trackName = MusicConfiguration.tracks[index].AudioClip != null
                ? MusicConfiguration.tracks[index].AudioClip.name
                : "<null>";

            if (i == _historyPointer)
                output += $"=> [{i}] {trackName}\n";
            else
                output += $"   [{i}] {trackName}\n";
        }

        Debug.Log(output);
    }
}

// --- End File: Unity\TargetOne\Assets\Core\Runtime\Music\MusicPlayer.cs ---


--------------------------------------------------
// --- Prompt ---

- Reviewing source files for a Music.
- Your task is to create a well-structured and user-friendly `README.md` that includes the following sections:

## Introduction
- Provide a brief overview of the tool from the user's perspective.
- Explain its purpose and the problem it solves.

## Features
- List the key capabilities of the tool as bullet points.

## Summary
- Conclude with a concise summary highlighting the module’s value and primary use case.

